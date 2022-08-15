from typing import List
from fastapi import UploadFile, APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter(prefix='/files', tags=["files"])


@router.post("/", status_code=201)
async def upload_files(files: List[UploadFile], username: str = Form()):
    return {
        "filenames": [f.filename for f in files],
        "username": username
    }


@router.get("/")
async def get_files_upload_form():
    return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <title>File Upload</title>
                <meta name="description" content="">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="stylesheet" href="">
            </head>
            <body>
                <form action="/files/" enctype="multipart/form-data" method="post">
                    <input name="username" type="text"></br>
                    <input name="files" type="file" multiple>
                    <input type="submit">
                </form>  
                <script src="" async defer></script>
            </body>
        </html>"""
    )
