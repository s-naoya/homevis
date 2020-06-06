#!/bin/bash
BACKUP_DIR=/backup

echo Start Homevis Backup at `date`

PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -Fc ${POSTGRES_DB} -h homevis_db -U ${POSTGRES_USER} --format=custom -f $BACKUP_DIR/$(date +%s_%F)_homevis_db_backup.dump

PGPASSWORD=${METABASE_PASSWORD} pg_dump -Fc ${METABASE_DB} -h homevis_metabase_db -U ${METABASE_USER} --format=custom -f $BACKUP_DIR/$(date +%s_%F)_metabase_db_backup.dump


### 古いバックアップファイルを削除
BACKUP_KEEP_TIME=604700  # 保持秒数 7*24*60*60-100で7日間設定

for pathfile in `ls -F $BACKUP_DIR | grep -v /`; do  # BACKUP_DIR内の全ファイル（ディレクトリを除外）
    utime=`echo $pathfile | cut -d'_' -f 1`  # ファイル名先頭のUNIX TIMEを抽出
    difftime=$(($(date +%s)-$utime))  # 現在時間とファイル作成時間の差分

    # difftimeがBACKUP_KEEP_TIME以上だった場合、対象ファイルを削除
    if [ $difftime -gt $BACKUP_KEEP_TIME ]; then
        echo delete $BACKUP_DIR/$pathfile
        rm $BACKUP_DIR/$pathfile
    fi
done

echo Finish Homevis Backup at `date`

