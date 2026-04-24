import base64
import io
import fitz  # PyMuPDF
import docx
from fastapi import UploadFile

def parse_files(files: list[UploadFile]) -> tuple[str, list[dict]]:
    """
    Xử lý danh sách upload file.
    Trả về:
    - extracted_text: Nội dung chữ gộp từ các file văn bản (.txt, .md, .csv, .pdf, .docx).
    - media_attachments: Mảng các object JSON chứa base64 media theo chuẩn OpenRouter.
    """
    extracted_text_blocks = []
    media_attachments = []

    for file in files:
        if not file.filename:
            continue
        
        filename = file.filename.lower()
        content = file.file.read()

        # 1. Xử lý File Text (txt, csv, md, json)
        if filename.endswith(".txt") or filename.endswith(".csv") or filename.endswith(".md") or filename.endswith(".json"):
            try:
                text = content.decode("utf-8")
                extracted_text_blocks.append(f"--- Bắt đầu nội dung file {file.filename} ---\n{text}\n--- Kết thúc file {file.filename} ---")
            except Exception as e:
                extracted_text_blocks.append(f"(Không thể đọc file text {file.filename}: {str(e)})")
        
        # 2. Xử lý PDF
        elif filename.endswith(".pdf"):
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                pdf_text = []
                for page in doc:
                    pdf_text.append(page.get_text())
                doc.close()
                extracted_text_blocks.append(f"--- Bắt đầu nội dung file {file.filename} ---\n{chr(10).join(pdf_text)}\n--- Kết thúc file {file.filename} ---")
            except Exception as e:
                extracted_text_blocks.append(f"(Không thể đọc file PDF {file.filename}: {str(e)})")
        
        # 3. Xử lý Word (.docx)
        elif filename.endswith(".docx"):
            try:
                doc = docx.Document(io.BytesIO(content))
                doc_text = [paragraph.text for paragraph in doc.paragraphs]
                extracted_text_blocks.append(f"--- Bắt đầu nội dung file {file.filename} ---\n{chr(10).join(doc_text)}\n--- Kết thúc file {file.filename} ---")
            except Exception as e:
                extracted_text_blocks.append(f"(Không thể đọc file DOCX {file.filename}: {str(e)})")
        
        # 4. Xử lý Hình ảnh
        elif file.content_type and file.content_type.startswith("image/"):
            b64_data = base64.b64encode(content).decode("utf-8")
            media_attachments.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{file.content_type};base64,{b64_data}"
                }
            })
            
        # 5. Xử lý Video
        elif file.content_type and file.content_type.startswith("video/"):
            b64_data = base64.b64encode(content).decode("utf-8")
            media_attachments.append({
                "type": "video_url",
                "video_url": {
                    "url": f"data:{file.content_type};base64,{b64_data}"
                }
            })
            
        # 6. Xử lý Audio
        elif file.content_type and (file.content_type.startswith("audio/") or file.content_type == "video/webm"): 
            # Một số trình duyệt ghi âm audio bằng webm (e.g. video/webm)
            b64_data = base64.b64encode(content).decode("utf-8")
            
            # Lấy phần mở rộng định dạng hoặc từ content type
            audio_format = "mp3"
            if "webm" in filename or "webm" in file.content_type:
                audio_format = "webm"
            elif "wav" in filename or "wav" in file.content_type:
                audio_format = "wav"
            elif "ogg" in filename or "ogg" in file.content_type:
                audio_format = "ogg"
            elif "mp4" in filename or "mp4" in file.content_type:
                audio_format = "mp4"

            media_attachments.append({
                "type": "input_audio",
                "input_audio": {
                    "data": b64_data,
                    "format": audio_format
                }
            })
        
        else:
            # File không xác định, có thể bỏ qua hoặc báo lỗi
            extracted_text_blocks.append(f"(File {file.filename} có định dạng không được hỗ trợ)")

    return "\n\n".join(extracted_text_blocks), media_attachments
