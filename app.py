import mysql.connector
from flask import Flask, render_template, request, redirect, session, flash, make_response, send_file, jsonify
import smtplib
from email.mime.text import MIMEText
from fpdf import FPDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
app = Flask(__name__)
app.secret_key = "Itssecret345"

# DATABASE CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Galaxy@8600",
    database="service_marketplace"
)

cursor = db.cursor()

# EMAIL FUNCTION
def send_email(to_email):
    sender = "servicehub0809@gmail.com"
    password = "wjcfrmejhogrzlcg"

    msg = MIMEText("Your registration on ServiceHub is successful!")
    msg["Subject"] = "Registration Successful"
    msg["From"] = sender
    msg["To"] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(sender, password)
    server.send_message(msg)
    server.quit()


# =================== HOME ===================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/services")
def services():
    return render_template("services.html")


# =================== USER LOGIN ===================

@app.route("/login-user", methods=["GET", "POST"])
def login_user():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Email not found")
            return redirect("/login-user")

        if user[4] != password:
            flash("Incorrect password")
            return redirect("/login-user")

        session["user_id"] = user[0]
        session["user_name"] = user[1]

        return redirect("/user-dashboard")

    return render_template("login_user.html")


# =================== USER REGISTER ===================

@app.route("/register-user", methods=["GET", "POST"])
def register_user():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if not name or not email or not phone or not password or not confirm:
            flash("All fields are required")
            return redirect("/register-user")

        if password != confirm:
            flash("Passwords must match")
            return redirect("/register-user")

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already exists")
            return redirect("/register-user")

        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (%s,%s,%s,%s)",
            (name, email, phone, password)
        )
        db.commit()

        send_email(email)

        flash("Registration successful! Now login.")
        return redirect("/login-user")

    return render_template("register_user.html")


# =================== USER DASHBOARD ===================

@app.route("/user-dashboard")
def user_dashboard():

    if "user_id" not in session:
        return redirect("/login-user")

    user_id = session["user_id"]

    # TOTAL BOOKINGS
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id=%s", (user_id,))
    total = cursor.fetchone()[0]

    # PENDING
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id=%s AND status='Pending'", (user_id,))
    pending = cursor.fetchone()[0]

    # COMPLETED
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id=%s AND status='Completed'", (user_id,))
    completed = cursor.fetchone()[0]

    # RECENT BOOKINGS
    cursor.execute("SELECT * FROM bookings WHERE user_id=%s ORDER BY id DESC LIMIT 5", (user_id,))
    recent = cursor.fetchall()

    return render_template(
        "user_dashboard.html",
        total=total,
        pending=pending,
        completed=completed,
        recent=recent
    )


# =================== BOOK SERVICE ===================

@app.route("/book/<service>", methods=["GET", "POST"])
def book_service(service):

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/login-user")

    if request.method == "POST":
        user_id = session["user_id"]

        service_name = request.form["service"]
        date = request.form["date"]
        time = request.form["time"]
        address = request.form["address"]
        description = request.form["description"]

        cursor.execute("""
            INSERT INTO bookings (user_id, service_name, date, time, address, description, status)
            VALUES (%s,%s,%s,%s,%s,%s,'Pending')
        """, (user_id, service_name, date, time, address, description))

        db.commit()

        flash("Booking successful!")
        return redirect("/my-bookings")

    return render_template("booking_form.html", service=service)


# =================== MY BOOKINGS ===================

@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login-user")

    user_id = session["user_id"]

    cursor.execute("""
    SELECT b.id, b.service_name, b.date, b.time, b.status,
           p.name, p.phone
    FROM bookings b
    LEFT JOIN providers p ON b.provider_id = p.id
    WHERE b.user_id=%s
""", (user_id,))


    bookings = cursor.fetchall()

    return render_template("my_bookings.html", bookings=bookings)



# =================== LOGOUT ===================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


#==================== Provider register=========#
@app.route("/register-provider", methods=["GET", "POST"])
def register_provider():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        service = request.form["service"]
        experience = request.form["experience"]
        address = request.form["address"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        # 🔴 1. CHECK EMPTY FIELDS
        if not name or not email or not phone or not service or not experience or not address or not password or not confirm:
            flash("All fields are required")
            return redirect("/register-provider")

        # 🔴 2. PASSWORD MATCH CHECK
        if password != confirm:
            flash("Passwords must match")
            return redirect("/register-provider")

        # 🔴 3. EMAIL UNIQUE CHECK
        cursor.execute("SELECT * FROM providers WHERE email=%s", (email,))
        existing = cursor.fetchone()

        if existing:
            flash("Email already registered")
            return redirect("/register-provider")

        # 🔴 4. INSERT PROVIDER
        query = """
        INSERT INTO providers
        (name, email, phone, service_type, experience, address, password)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        values = (name, email, phone, service, experience, address, password)

        cursor.execute(query, values)
        db.commit()

        # 🔴 5. SEND EMAIL
        send_email(email)

        # 🔴 6. SUCCESS MESSAGE
        flash("Registration successful! Now you can login.")

        return redirect("/login-provider")

    return render_template("register_provider.html")

#==================== login provider============#
@app.route("/login-provider", methods=["GET", "POST"])
def login_provider():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # 🔴 CHECK EMAIL EXISTS
        cursor.execute("SELECT * FROM providers WHERE email=%s", (email,))
        provider = cursor.fetchone()

        if not provider:
            flash("Email not found")
            return redirect("/login-provider")

        # 🔴 CHECK PASSWORD MATCH
        if provider[7] != password:
            flash("Incorrect password")
            return redirect("/login-provider")

        # 🟢 LOGIN SUCCESS
        session["provider_id"] = provider[0]
        session["provider_name"] = provider[1]
        session["provider_service"] = provider[4]

        flash("Login successful!")

        return redirect("/provider-dashboard")

    return render_template("login_provider.html")
# =================== provider dashboard ===================
@app.route("/provider-dashboard")
def provider_dashboard():

    if "provider_id" not in session:
        return redirect("/login-provider")

    provider_id = session["provider_id"]
    service = session["provider_service"]

    # 🔹 TOTAL BOOKINGS FOR THIS SERVICE
    cursor.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE service_name=%s
    """, (service,))
    total = cursor.fetchone()[0]

    # 🔹 PENDING BOOKINGS
    cursor.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE service_name=%s AND status='Pending'
    """, (service,))
    pending = cursor.fetchone()[0]

    # 🔹 COMPLETED BOOKINGS
    cursor.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE provider_id=%s AND status='Completed'
    """, (provider_id,))
    completed = cursor.fetchone()[0]

    # 🔹 RECENT REQUESTS (JOIN USERS TABLE)
    cursor.execute("""
        SELECT u.name, b.service_name, b.date, b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.service_name=%s
        ORDER BY b.id DESC
        LIMIT 5
    """, (service,))

    recent = cursor.fetchall()

    return render_template(
        "provider_dashboard.html",
        total=total,
        pending=pending,
        completed=completed,
        recent=recent
    )

#==================== view request at provider side======
@app.route("/provider-requests")
def provider_requests():

    if "provider_id" not in session:
        return redirect("/login-provider")

    provider_id = session["provider_id"]

    # get provider service type
    cursor.execute("SELECT service_type FROM providers WHERE id=%s", (provider_id,))
    service = cursor.fetchone()[0]

    # show ALL bookings of that service
    cursor.execute("""
        SELECT b.id, u.name, u.phone, b.service_name, b.date, b.time,
               b.address, COALESCE(b.status,'Pending')
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.service_name=%s
        AND (b.status IS NULL OR b.status!='Completed')
        ORDER BY b.date DESC
    """, (service,))

    requests = cursor.fetchall()

    return render_template("provider_requests.html", requests=requests)

#===================== accept request ==========
@app.route("/accept-booking/<int:id>")
def accept_booking(id):

    if "provider_id" not in session:
        return redirect("/login-provider")

    provider_id = session["provider_id"]

    cursor.execute("""
        UPDATE bookings
        SET status='Accepted', provider_id=%s
        WHERE id=%s
    """, (provider_id, id))

    db.commit()

    return redirect("/provider-requests")


#=================== reject request ============
@app.route("/reject-booking/<int:id>")
def reject_booking(id):

    cursor.execute("""
        UPDATE bookings
        SET status='Rejected'
        WHERE id=%s
    """, (id,))

    db.commit()

    return redirect("/provider-requests")


#=================== provider job history========
@app.route("/provider-history")
def provider_history():

    if "provider_id" not in session:
        return redirect("/login-provider")

    provider_id = session["provider_id"]

    query = """
    SELECT u.name, u.phone, b.service_name, b.date, b.address
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    WHERE b.provider_id=%s AND b.status='Completed'
    ORDER BY b.date DESC
    """

    cursor.execute(query, (provider_id,))
    history = cursor.fetchall()

    return render_template("provider_history.html", history=history)
#=================== provider confirmation========
@app.route("/mark-provider-done/<int:booking_id>")
def mark_provider_done(booking_id):

    if "provider_id" not in session:
        return redirect("/login-provider")

    cursor.execute("""
        UPDATE bookings
        SET status='Provider_Completed'
        WHERE id=%s
    """, (booking_id,))

    db.commit()

    return redirect("/provider-requests")

#=================== user confirmation===========
@app.route("/confirm-completion/<int:booking_id>")
def user_confirm_completion(booking_id):

    if "user_id" not in session:
        return redirect("/login-user")

    cursor.execute("""
        UPDATE bookings
        SET status='Completed'
        WHERE id=%s
    """, (booking_id,))

    db.commit()

    flash("Service marked as completed!")
    return redirect("/my-bookings")

#===================admin section===============
#====================admin login================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (username, password)
        )

        admin = cursor.fetchone()

        if admin:
            session["admin"] = admin[0]
            session["admin_name"] = admin[1]
            flash("Login successful!")
            return redirect("/admin-dashboard")

        else:
            flash("Invalid credentials!")
            return redirect("/admin-login")

    return render_template("admin_login.html")

#====================admin dashboard============
@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin-login")

    # COUNT DATA
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM providers")
    total_providers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        users=total_users,
        providers=total_providers,
        bookings=total_bookings
    )

#===================change admin password=======
@app.route("/admin-change-password", methods=["GET", "POST"])
def admin_change_password():

    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":

        old = request.form["old"]
        new = request.form["new"]
        confirm = request.form["confirm"]

        # Check old password
        cursor.execute(
            "SELECT password FROM admin WHERE id=%s",
            (session["admin"],)
        )

        current = cursor.fetchone()[0]

        if old != current:
            flash("Old password incorrect!")
            return redirect("/admin-change-password")

        if new != confirm:
            flash("Passwords do not match!")
            return redirect("/admin-change-password")

        cursor.execute(
            "UPDATE admin SET password=%s WHERE id=%s",
            (new, session["admin"])
        )

        db.commit()

        flash("Password changed successfully!")
        return redirect("/admin-dashboard")

    return render_template("admin_change_password.html")

#===================== admin reports============#
@app.route("/admin-reports")
def admin_reports():

    if "admin" not in session:
        return redirect("/admin-login")

    # 1️⃣ Pending / Completed
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Completed'")
    completed = cursor.fetchone()[0]

    # 2️⃣ Most booked services
    cursor.execute("""
        SELECT service_name, COUNT(*)
        FROM bookings
        GROUP BY service_name
    """)
    serviceData = cursor.fetchall()

    services = [row[0] for row in serviceData]
    counts = [row[1] for row in serviceData]

    # 3️⃣ Monthly bookings trend
    cursor.execute("""
        SELECT MONTH(date), COUNT(*)
        FROM bookings
        GROUP BY MONTH(date)
        ORDER BY MONTH(date)
    """)
    monthData = cursor.fetchall()

    months = [f"Month {row[0]}" for row in monthData]
    monthCounts = [row[1] for row in monthData]

    return render_template(
        "admin_reports.html",
        pending=pending,
        completed=completed,
        services=services,
        counts=counts,
        months=months,
        monthCounts=monthCounts
    )
#==================== analytics report pdf=======
@app.route("/export-analytics")
def export_analytics():

    if "admin" not in session:
        return redirect("/admin-login")

    # ===== Booking Status =====
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Completed'")
    completed = cursor.fetchone()[0]

    # ===== Most Booked Services =====
    cursor.execute("""
        SELECT service_name, COUNT(*)
        FROM bookings
        GROUP BY service_name
        ORDER BY COUNT(*) DESC
    """)
    services = cursor.fetchall()

   # ===== Monthly Stats =====
    cursor.execute("""
        SELECT DATE_FORMAT(date,'%b %Y') AS month,
           COUNT(*) AS total
        FROM bookings
        GROUP BY DATE_FORMAT(date,'%b %Y')
        ORDER BY MIN(date)
    """)

    months = cursor.fetchall()


    # ===== Create PDF =====
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("ServiceHub Analytics Report", styles['Title']))
    elements.append(Spacer(1, 20))

    # ===== Booking Summary =====
    summary_data = [
        ["Metric", "Count"],
        ["Pending Bookings", pending],
        ["Completed Bookings", completed]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))

    elements.append(Paragraph("Booking Summary", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 25))

    # ===== Most Booked Services =====
    service_data = [["Service", "Total Bookings"]]

    for s in services:
        service_data.append([s[0], s[1]])

    service_table = Table(service_data)
    service_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))

    elements.append(Paragraph("Most Booked Services", styles['Heading2']))
    elements.append(service_table)
    elements.append(Spacer(1, 25))

    # ===== Monthly Trend =====
    month_data = [["Month", "Bookings"]]

    for m in months:
        month_data.append([m[0], m[1]])

    month_table = Table(month_data)
    month_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))

    elements.append(Paragraph("Monthly Booking Trend", styles['Heading2']))
    elements.append(month_table)

    pdf.build(elements)
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="analytics_report.pdf",
                     mimetype="application/pdf")

#===================admin users manage===========
@app.route("/admin-users")
def admin_users():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("SELECT id, name, email, phone FROM users")
    users = cursor.fetchall()

    return render_template("admin_users.html", users=users)
#================delete user====================
@app.route("/admin-delete-user/<int:id>")
def admin_delete_user(id):

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    db.commit()

    return redirect("/admin-users")
#=================== export user pdf===========
@app.route("/export-users")
def export_users():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("SELECT id, name, email, phone FROM users")
    users = cursor.fetchall()

    pdf = create_pdf("Users Report")

    pdf.set_font("Arial", "", 12)

    for u in users:
        pdf.cell(0, 10,
                 f"ID: {u[0]} | Name: {u[1]} | Email: {u[2]} | Phone: {u[3]}",
                 0, 1)

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=users_report.pdf'

    return response

#=================== admin show provider========
@app.route("/admin-providers")
def admin_providers():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("""
        SELECT id, name, email, phone, service_type, experience, address
        FROM providers
    """)

    providers = cursor.fetchall()

    return render_template("admin_providers.html", providers=providers)

#====================export provider pdf========
@app.route("/export-providers")
def export_providers():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("SELECT id,name,email,phone,service_type,experience,address FROM providers")
    providers = cursor.fetchall()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("ServiceHub - Providers Report", styles['Title']))
    elements.append(Spacer(1, 20))

    # Table Data
    data = [["ID","Name","Email","Phone","Service","Experience","Address"]]

    for p in providers:
        data.append(list(p))

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('BACKGROUND',(0,1),(-1,-1), colors.whitesmoke),
        ('BOTTOMPADDING',(0,0),(-1,0),12),
    ]))

    elements.append(table)

    pdf.build(elements)
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="providers_report.pdf",
                     mimetype='application/pdf')

#====================delete provider===========
@app.route("/admin-delete-provider/<int:id>")
def admin_delete_provider(id):

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("DELETE FROM providers WHERE id=%s", (id,))
    db.commit()

    return redirect("/admin-providers")

#=================== admin view booking section=========
@app.route("/admin-bookings")
def admin_bookings():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("""
        SELECT 
            b.id,
            u.name,
            IFNULL(p.name, 'Not Assigned'),
            b.service_name,
            b.date,
            b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN providers p ON b.provider_id = p.id
        ORDER BY b.id DESC
    """)

    bookings = cursor.fetchall()

    return render_template("admin_bookings.html", bookings=bookings)
#===================== bookings pdf===========

@app.route("/export-bookings")
def export_bookings():

    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("""
        SELECT b.id, u.name, p.name, b.service_name, b.date, b.status
        FROM bookings b
        LEFT JOIN users u ON b.user_id = u.id
        LEFT JOIN providers p ON b.provider_id = p.id
        ORDER BY b.id DESC
    """)

    bookings = cursor.fetchall()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("ServiceHub - Bookings Report", styles['Title']))
    elements.append(Spacer(1, 20))

    # Table Data
    data = [["ID","User","Provider","Service","Date","Status"]]

    for b in bookings:
        data.append([
            b[0],
            b[1] or "Not Assigned",
            b[2] or "Pending",
            b[3],
            str(b[4]),
            b[5]
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('BACKGROUND',(0,1),(-1,-1), colors.whitesmoke),
        ('BOTTOMPADDING',(0,0),(-1,0),12),
    ]))

    elements.append(table)

    pdf.build(elements)
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="bookings_report.pdf",
                     mimetype='application/pdf')

#--------------------- pdf method--------------
def create_pdf(title):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ServiceHub Report", 0, 1, "C")

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, 0, 1)

    pdf.ln(5)

    return pdf

#==================== about page================
@app.route("/about")
def about():
    return render_template("about.html")

# =================== TEST DB ===================

@app.route("/test-db")
def test_db():
    cursor.execute("SELECT * FROM users")
    return str(cursor.fetchall())


# =================== RUN ===================

if __name__ == "__main__":
    app.run(debug=True)
