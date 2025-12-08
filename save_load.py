import os


SAVE_FILE = 'save.json'


def delete_save() -> bool:
    """
    删除本地 JSON 存档文件。

    当前版本统一使用数据库存档，本模块仅作为清理旧版本地存档的辅助工具。
    """
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
            return True
        return False
    except Exception:
        return False
