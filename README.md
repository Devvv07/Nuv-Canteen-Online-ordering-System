# 🍽️ NUV Canteen Ordering System

A **Python Tkinter–based desktop application** designed for **Navrachana University Canteen**. This system allows students to log in, browse the menu, order food (including daily thali), make payments (Cash / Online via QR), and view order history. It also includes an **Admin Panel** for menu management and basic analytics.

---

## ✨ Features

### 👨‍🎓 Student Side

* Student **Login & Signup**
* **Weekly Thali Menu** with current-day highlight
* Fast Food & Beverage menu
* Add items to cart (double-click)
* Half / Full Thali option
* Remove items from cart
* Order confirmation dialog
* **Payment options**:

  * Cash
  * Online (QR Code + UPI ID entry)
* Auto-generated **Bill window**
* View **Order History**
* Dark / Light mode toggle

### 🛠️ Admin Panel

* Password-protected Admin login
* Add new menu items
* Remove existing menu items
* View basic analytics:

  * Total orders
  * Total revenue

### 🎨 UI Enhancements

* Blurred background using `nuv.png`
* Clean Tkinter layout with Treeview tables
* Modal dialogs for confirmation & billing

---

## 🧰 Tech Stack

* **Language:** Python 3
* **GUI:** Tkinter, ttk
* **Database:** MySQL
* **Images & QR:** Pillow, qrcode

---

## 📁 Project Structure

```
NUV-Canteen-Ordering-System/
│
├── Nuv_Canteen_Project.py
├── nuv.png              # Background image (optional)
├── nuv.ico              # App icon (optional)
└── README.md
```

---

## 🗄️ Database Schema (MySQL)

### users

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    student_id VARCHAR(50),
    phone VARCHAR(15),
    password VARCHAR(100)
);
```

### menu_items

```sql
CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price FLOAT,
    category VARCHAR(50)
);
```

### orders

```sql
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50),
    item_desc TEXT,
    price FLOAT,
    date_for DATE,
    payment_method VARCHAR(20)
);
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/NUV-Canteen-Ordering-System.git
cd NUV-Canteen-Ordering-System
```

### 2️⃣ Install Dependencies

```bash
pip install mysql-connector-python pillow qrcode
```

### 3️⃣ Configure Database

Edit in `Nuv_Canteen_Project.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "navrachana_canteen"
}
```

### 4️⃣ Run Application

```bash
python Nuv_Canteen_Project.py
```

---

## 🔐 Admin Login

* **Default Admin Password:** `admin123`

> ⚠️ Change this password before production use.

---

## 🚀 Future Enhancements

* Real payment gateway integration
* Email / SMS order confirmation
* Role-based admin accounts
* Report export (CSV / PDF)
* Cloud database support

---

## 👤 Author

**Dev Mohite**
BSc Data Science – 2nd Year
Python | Tkinter | MySQL

---


⭐ If you like this project, don’t forget to **star** the repository!
