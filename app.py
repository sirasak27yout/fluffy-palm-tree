import os, calendar
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "CHANGE-THIS-SECRET-KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///fulaer_hr.db").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100), default="")
    position = db.Column(db.String(100), default="")
    salary = db.Column(db.Numeric(12,2), default=0)
    start_date = db.Column(db.Date, default=date.today)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="employee")
    active = db.Column(db.Boolean, default=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    work_date = db.Column(db.Date, nullable=False, default=date.today)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    note = db.Column(db.String(250), default="")
    __table_args__ = (db.UniqueConstraint("employee_id", "work_date"),)

class PayrollAdjustment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    pay_year = db.Column(db.Integer, nullable=False)
    pay_month = db.Column(db.Integer, nullable=False)
    allowance = db.Column(db.Numeric(12,2), default=0)
    ot_hours = db.Column(db.Numeric(8,2), default=0)
    other_deduction = db.Column(db.Numeric(12,2), default=0)
    note = db.Column(db.String(250), default="")
    __table_args__ = (db.UniqueConstraint("employee_id", "pay_year", "pay_month"),)

def current_user():
    if "user_id" not in session: return None
    return db.session.get(Employee, session["user_id"])

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        u=current_user()
        if not u: return redirect(url_for("login"))
        if u.role != "admin":
            flash("หน้านี้สำหรับ HR/Admin เท่านั้น", "danger")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    return dict(me=current_user(), today=date.today())

@app.route("/")
def index():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        code=request.form.get("employee_code","").strip()
        pw=request.form.get("password","")
        u=Employee.query.filter_by(employee_code=code, active=True).first()
        if u and check_password_hash(u.password_hash,pw):
            session.clear(); session["user_id"]=u.id
            return redirect(url_for("dashboard"))
        flash("รหัสพนักงานหรือรหัสผ่านไม่ถูกต้อง", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    u=current_user()
    if u.role=="admin":
        employees=Employee.query.filter_by(active=True).count()
        records=Attendance.query.filter_by(work_date=date.today()).all()
        checked=sum(1 for a in records if a.check_in)
        return render_template("dashboard.html", employees=employees, checked=checked, records=records)
    record=Attendance.query.filter_by(employee_id=u.id,work_date=date.today()).first()
    return render_template("dashboard.html", record=record)

@app.route("/punch/<action>", methods=["POST"])
@login_required
def punch(action):
    if current_user().role=="admin":
        flash("บัญชี HR ไม่สามารถลงเวลาแทนพนักงานได้", "warning")
        return redirect(url_for("dashboard"))
    if action not in ("in","out"): return redirect(url_for("dashboard"))
    u=current_user(); today=date.today()
    a=Attendance.query.filter_by(employee_id=u.id,work_date=today).first()
    if not a:
        a=Attendance(employee_id=u.id,work_date=today); db.session.add(a)
    now=datetime.now()
    if action=="in":
        if a.check_in: flash("วันนี้คุณเช็กอินแล้ว", "warning")
        else: a.check_in=now; flash("บันทึกเวลาเข้างานแล้ว", "success")
    else:
        if not a.check_in: flash("กรุณาเช็กอินก่อนเช็กเอาต์", "warning")
        elif a.check_out: flash("วันนี้คุณเช็กเอาต์แล้ว", "warning")
        else: a.check_out=now; flash("บันทึกเวลาออกงานแล้ว", "success")
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/employees", methods=["GET","POST"])
@admin_required
def employees():
    if request.method=="POST":
        try:
            emp=Employee(employee_code=request.form["employee_code"].strip(),
                full_name=request.form["full_name"].strip(),
                department=request.form.get("department","").strip(),
                position=request.form.get("position","").strip(),
                salary=Decimal(request.form.get("salary","0") or "0"),
                start_date=date.fromisoformat(request.form["start_date"]),
                password_hash=generate_password_hash(request.form["password"]),
                role=request.form.get("role","employee"))
            db.session.add(emp); db.session.commit()
            flash("เพิ่มข้อมูลพนักงานสำเร็จ", "success")
        except Exception as e:
            db.session.rollback(); flash("บันทึกไม่สำเร็จ: ตรวจสอบรหัสพนักงานและข้อมูลที่กรอก", "danger")
        return redirect(url_for("employees"))
    items=Employee.query.order_by(Employee.employee_code).all()
    return render_template("employees.html", employees=items)

@app.route("/attendance")
@admin_required
def attendance():
    month=int(request.args.get("month",date.today().month))
    year=int(request.args.get("year",date.today().year))
    rows=Attendance.query.filter(db.extract("month",Attendance.work_date)==month,
        db.extract("year",Attendance.work_date)==year).order_by(Attendance.work_date.desc()).all()
    return render_template("attendance.html", rows=rows, month=month, year=year)

@app.route("/payroll", methods=["GET","POST"])
@admin_required
def payroll():
    month=int(request.values.get("month",date.today().month))
    year=int(request.values.get("year",date.today().year))
    if request.method=="POST":
        emp_id=int(request.form["employee_id"])
        adj=PayrollAdjustment.query.filter_by(employee_id=emp_id,pay_month=month,pay_year=year).first()
        if not adj:
            adj=PayrollAdjustment(employee_id=emp_id,pay_month=month,pay_year=year); db.session.add(adj)
        adj.allowance=Decimal(request.form.get("allowance","0") or "0")
        adj.ot_hours=Decimal(request.form.get("ot_hours","0") or "0")
        adj.other_deduction=Decimal(request.form.get("other_deduction","0") or "0")
        adj.note=request.form.get("note","")
        db.session.commit(); flash("บันทึกรายการเงินเดือนแล้ว","success")
        return redirect(url_for("payroll",month=month,year=year))
    emps=Employee.query.filter_by(active=True).order_by(Employee.employee_code).all()
    results=[]
    for e in emps:
        adj=PayrollAdjustment.query.filter_by(employee_id=e.id,pay_month=month,pay_year=year).first()
        adj=adj or PayrollAdjustment(allowance=0,ot_hours=0,other_deduction=0)
        # ตัวอย่าง OT: เงินเดือน / 30 / 8 x 1.5 x ชั่วโมง (ต้องปรับตามนโยบายและกฎหมาย)
        ot=(Decimal(e.salary or 0)/Decimal(30)/Decimal(8)*Decimal("1.5")*Decimal(adj.ot_hours or 0))
        gross=Decimal(e.salary or 0)+Decimal(adj.allowance or 0)+ot
        net=gross-Decimal(adj.other_deduction or 0)
        results.append(dict(employee=e,adj=adj,ot=ot,gross=gross,net=net))
    return render_template("payroll.html",results=results,employees=emps,month=month,year=year)

@app.route("/payroll/export")
@admin_required
def payroll_export():
    month=int(request.args.get("month",date.today().month)); year=int(request.args.get("year",date.today().year))
    emps=Employee.query.filter_by(active=True).order_by(Employee.employee_code).all()
    lines=["รหัสพนักงาน,ชื่อ,แผนก,เงินเดือน,เบี้ยเลี้ยง,OT ชั่วโมง,ค่า OT,รายการหักอื่น,ยอดสุทธิ"]
    for e in emps:
        a=PayrollAdjustment.query.filter_by(employee_id=e.id,pay_month=month,pay_year=year).first()
        allowance=Decimal(a.allowance or 0) if a else Decimal(0)
        hours=Decimal(a.ot_hours or 0) if a else Decimal(0)
        deduction=Decimal(a.other_deduction or 0) if a else Decimal(0)
        ot=Decimal(e.salary or 0)/30/8*Decimal("1.5")*hours
        net=Decimal(e.salary or 0)+allowance+ot-deduction
        vals=[e.employee_code,e.full_name,e.department,str(e.salary),str(allowance),str(hours),str(ot.quantize(Decimal(".01"))),str(deduction),str(net.quantize(Decimal(".01")))]
        lines.append(",".join('"'+str(v).replace('"','""')+'"' for v in vals))
    csv="\ufeff"+"\n".join(lines)
    return Response(csv,mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename=payroll_{year}_{month:02}.csv"})

with app.app_context():
    db.create_all()
    if not Employee.query.filter_by(employee_code="HR001").first():
        admin=Employee(employee_code="HR001",full_name="ผู้ดูแลระบบ HR",department="HR",
            position="Administrator",salary=0,start_date=date.today(),
            password_hash=generate_password_hash(os.environ.get("ADMIN_PASSWORD","ChangeMe123!")),role="admin")
        db.session.add(admin); db.session.commit()

if __name__=="__main__":
    app.run(debug=True)
