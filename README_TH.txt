FULAER HR MANAGEMENT SYSTEM - คู่มือติดตั้งฉบับเริ่มต้น

ความสามารถในชุดต้นแบบ
- เข้าสู่ระบบด้วยรหัสพนักงานและรหัสผ่าน
- HR เพิ่มข้อมูลพนักงานและกำหนดบัญชี HR/พนักงาน
- พนักงานเช็กอินและเช็กเอาต์ผ่านเว็บไซต์
- HR ดูรายการลงเวลาแยกเดือน
- บันทึกเบี้ยเลี้ยง ชั่วโมง OT และรายการหักอื่น
- คำนวณยอดเงินเดือนสุทธิตัวอย่างและส่งออก CSV

ติดตั้งทดสอบบนเครื่องคอมพิวเตอร์
1) ติดตั้ง Python 3.11 หรือใหม่กว่า
2) แตกไฟล์ ZIP
3) เปิด Terminal/Command Prompt ในโฟลเดอร์โปรแกรม
4) สร้าง virtual environment:
   python -m venv .venv
5) เปิดใช้งาน:
   Windows: .venv\Scripts\activate
   Mac: source .venv/bin/activate
6) ติดตั้ง:
   pip install -r requirements.txt
7) ตั้งรหัสผ่านผู้ดูแลระบบก่อนเริ่ม:
   Windows PowerShell: $env:ADMIN_PASSWORD="รหัสผ่านที่คาดเดายาก"
   Mac/Linux: export ADMIN_PASSWORD="รหัสผ่านที่คาดเดายาก"
8) ตั้ง SECRET_KEY เป็นค่าสุ่มที่ยาวและเป็นความลับ:
   Windows PowerShell: $env:SECRET_KEY="ค่าสุ่มยาวๆ"
   Mac/Linux: export SECRET_KEY="ค่าสุ่มยาวๆ"
9) เริ่มโปรแกรม:
   python app.py
10) เปิดเว็บ http://127.0.0.1:5000
บัญชีเริ่มต้น: HR001 และรหัสผ่านตาม ADMIN_PASSWORD ที่ตั้งไว้
ถ้าไม่ได้ตั้ง ADMIN_PASSWORD จะใช้ ChangeMe123! (ห้ามใช้ในระบบจริง)

แนวทางนำขึ้นเว็บไซต์ (ตัวอย่าง Render)
1) สมัคร GitHub และ Render
2) สร้าง GitHub repository แบบ Private
3) อัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้เข้า repository
4) Render > New > Web Service > เชื่อม GitHub repository
5) Build Command: pip install -r requirements.txt
6) Start Command: gunicorn app:app
7) เพิ่ม Environment Variables:
   SECRET_KEY = ค่าสุ่มยาว
   ADMIN_PASSWORD = รหัสผ่านเริ่มต้นที่แข็งแรง
   DATABASE_URL = URL ของ PostgreSQL ที่สร้างบน Render
8) Deploy แล้วเปิด URL ที่ Render ให้

สำคัญ:
- SQLite เหมาะสำหรับทดลองในเครื่องเท่านั้น การใช้งานจริงบนโฮสต์ควรใช้ PostgreSQL และตั้งค่า backup
- ระบบนี้เป็น MVP/ต้นแบบ ไม่ใช่ระบบ payroll ที่ผ่านการตรวจสอบกฎหมายหรือความปลอดภัยสำหรับ production
- สูตร OT เป็นตัวอย่าง 1.5 เท่า และหาร 30/8 เท่านั้น ต้องปรับตามประเภทวันทำงาน วันหยุด และกฎหมายแรงงาน
- ยังไม่ได้คำนวณภาษีหัก ณ ที่จ่าย ประกันสังคม กองทุนสำรองเลี้ยงชีพ วันลา วันหยุดนักขัตฤกษ์ กะงาน หรือการอนุมัติ OT
- ก่อนใช้จริงควรเพิ่มการแก้ไข/ปิดบัญชีพนักงาน, reset password, role permissions แบบละเอียด, audit log, backup/restore, HTTPS, rate limiting, MFA และทดสอบสิทธิ์การเข้าถึง
- อย่าใช้ข้อมูลพนักงานจริงหรือข้อมูลเงินเดือนจริงในระบบทดลอง
