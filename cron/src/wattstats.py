#!/usr/bin/env python3
# encoding utf-8
"""電力消費量を取得し、データベースに追加・更新

Args: 日付を選択。下記のどちらかを入力可能
    "new" -- スクリプトを稼働した日から三日前まで。str
    from_date to_date -- 指定した日付間。8桁のint×2
"""
import os
import sys
from re import split
from io import StringIO
from datetime import date, datetime, timedelta

import requests
import pandas as pd
import psycopg2

from logger import Logger

log = Logger("wattstats")


def parser(args):
    """引数からデータ取得対象の日付を計算

    Arguments:
        args {[str] or [int, int]} -- コマンドライン引数

    Returns:
        [datetime] -- 取得対象の日付のリスト
    """
    from_to_date = [None, None]  # [datetime, datetime]

    if len(args) == 2 and args[1] == "new":
        # 引数が"new"のみの場合、起動日の3日前から前日までを指定
        today = datetime.today()
        from_to_date[0] = today-timedelta(days=3)
        from_to_date[1] = today-timedelta(days=1)
    elif len(args) == 3 and len(args[1]) == 8 and len(args[2]) == 8:
        # 引数が2つかつ引数の長さが8の場合、引数1から引数2までを指定
        for i in range(2):
            try:
                from_to_date[i] = datetime.strptime(args[i+1], "%Y%m%d")
            except ValueError as e:
                log.error("The argument of from_to_date "
                          "must be in YYYYMMDD format "+str(e))
                sys.exit(1)
    else:
        log.error("The argument can be the string 'new' or"
                  "an 8-digit*2 integer 'from_date to_date'. "
                  + "arguments -> "
                  + " ".join(args))
        sys.exit(1)

    log.info("from_date: " + datetime.strftime(from_to_date[0], '%Y-%m-%d')
             + "  to_date: " + datetime.strftime(from_to_date[1], '%Y-%m-%d'))

    # from-to間の全日付をdatelistに格納
    days_num = (from_to_date[1] - from_to_date[0]).days + 1
    datelist = []
    for i in range(days_num):
        day = from_to_date[0] + timedelta(days=i)
        datelist.append((day.year, day.month, day.day))
    return datelist


def login(session):
    # ログイン情報設定
    username = os.environ["TEPCO_USERNAME"]
    password = os.environ["TEPCO_PASSWORD"]

    # ログイン 念のため一度トップページへアクセスしてcookieを取得
    loginparam = {
        'ACCOUNTUID': username,
        'PASSWORD': password,
        'HIDEURL': '/pf/ja/pc/mypage/home/index.page?',
        'LOGIN': 'EUAS_LOGIN',
    }
    loginheader = {
        'Referer': 'https://www.kurashi.tepco.co.jp/kpf-login',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    session.get('https://www.kurashi.tepco.co.jp/kpf-login')
    login = session.post(
        'https://www.kurashi.tepco.co.jp/kpf-login',
        data=loginparam, headers=loginheader
    )
    log.debug("success tepco login")


def csv(session, dates):
    # 使用量ページの cookie を取得
    url_comparison = ("https://www.kurashi.tepco.co.jp"
                      "/pf/ja/pc/mypage/learn/comparison.page")
    session.get(url_comparison)

    df = pd.DataFrame()
    for date in dates:
        # URL を組み立てて CSV データを取得
        csv_url = url_comparison + '?ReqID=CsvDL&year=' + str(date[0])
        csv_url += '&month=%00d&day=%00d' % (date[1], date[2])
        csvgetheader = {'Referer': url_comparison}
        csvdata = session.get(csv_url, headers=csvgetheader)

        # CSVをDataFrameに読み込み
        try:
            df_tmp = pd.read_csv(StringIO(csvdata.text))
        except Exception as e:
            log.error("Don't read csv "
                      + str(date[0]) + "-" + str(date[1]) + "-" + str(date[2])
                      + " " + str(e))
            continue
        df = pd.concat([df, df_tmp])

    # 不要な列を削除
    df = df.drop("お客さま番号", axis=1)
    df = df.drop("事業所コード", axis=1)
    df = df.drop("ご請求番号", axis=1)
    df = df.drop("供給地点特定番号", axis=1)
    df = df.drop("休祝日", axis=1)
    df = df.drop("契約メニュー", axis=1)
    df = df.drop("曜日", axis=1)

    # ヘッダー名称を変更
    df = df.rename(columns={
        "年月日": "datetime",
        "ご使用量": "watt_usage",
        "売電量": "watt_sold"
    })

    def over24h_2_datetime(x):
        # tepcoの日付をdatetime型に変換 24:00になっている場合翌日の00:00に変換
        dts = split("[/ :]", x)  # 0year, 1month, 2day, 3hour, 4minute
        minutes = int(dts[3])*60 + int(dts[4])
        dt = datetime(year=int(dts[0]), month=int(dts[1]), day=int(dts[2]))
        dt += timedelta(minutes=minutes)
        return dt

    # 稀に含まれる"---"を変換
    df = df.fillna(0)
    df = df.astype({"watt_usage": str})
    df = df.astype({"watt_sold": str})
    df = df.replace({"watt_usage": {"---": "0.0"}})
    df = df.replace({"watt_sold": {"---": "0.0"}})
    df = df.astype({"watt_usage": float})
    df = df.astype({"watt_sold": float})
    # 日付を適切なものに変換
    df["datetime"] = df["datetime"].map(over24h_2_datetime)

    return df


def todb(df):
    database_url = 'postgresql://%s:%s@%s:5432/%s' % (
        os.environ["POSTGRES_USER"],
        os.environ["POSTGRES_PASSWORD"],
        "homevis_db",
        os.environ["POSTGRES_DB"],
    )
    log.debug("connect "+os.environ["POSTGRES_DB"]+" database")

    with psycopg2.connect(database_url) as con:
        with con.cursor() as cur:
            for _, row in df.iterrows():
                update_watt(con, cur, row)


def update_watt(con, cur, row):
    try:
        cur.execute(
            "INSERT INTO wattstats(datetime, watt_usage, watt_sold)"
            " VALUES(%(dt)s, %(wu)s, %(ws)s) "
            "ON CONFLICT (datetime) "
            "DO UPDATE SET watt_usage = %(wu)s, watt_sold = %(ws)s;",
            {"dt": row.datetime, "wu": row.watt_usage, "ws": row.watt_sold}
        )
    except Exception as e:
        log.error("Error update watt: "
                  + datetime.strftime(row.datetime, '%Y-%m-%d %h:%m:%s')
                  + " " + str(e))
        con.rollback()
    else:
        con.commit()


def getkmhs(dates):
    session = requests.Session()
    login(session)
    df = csv(session, dates)
    return df


if __name__ == '__main__':
    log.info("Run wattstats.py")

    try:
        ymd = parser(sys.argv)
        df = getkmhs(ymd)
        todb(df)
    except Exception as e:
        log.error("Some kind of error has occurred: "+str(e))

    log.info("Finish wattstats.py")
