import os
import shutil
import json

from typing import Any, Callable


def upsert_folder(folder_path: str, debug_prn: bool = False, replace_folder=False):

    # Treat folder_path as a folder, not a file
    if replace_folder and os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

    if debug_prn:
        print(
            {
                "upsert_folder": os.path.abspath(folder_path),
                "is_exist": os.path.exists(folder_path),
            }
        )

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def write_fn_json(file, content: dict) -> None:
    return json.dump(content, file, indent=2, ensure_ascii=False)


def upsert_file(
    file_path: str,
    content: Any = None,
    write_fn: Callable = None,
    file_update_method="w",
    encoding="utf-8",
    debug_prn: bool = False,
    replace_folder: bool = False,
) -> bool:

    folder_path = (
        file_path if not os.path.splitext(file_path)[1] else os.path.dirname(file_path)
    )

    upsert_folder(
        folder_path=folder_path, debug_prn=debug_prn, replace_folder=replace_folder
    )

    with open(file_path, file_update_method, encoding=encoding) as file:
        if not write_fn:
            file.write(content or "")
            return True

        return write_fn(file=file, content=content)
