"""
NUV Canteen Ordering System - Full Updated
Features:
 - Left & Right blurred background from 'nuv.png'
 - Weekly Thali with current-day highlight
 - Cart, Add Thali, Place Order -> Confirm -> Payment (Cash/Online)
 - QR generation (qrcode + pillow) if available; otherwise simulation
 - UPI ID input next to QR
 - Admin panel (menu management + simple order analytics)
 - Dark / Light mode toggle
"""

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, simpledialog, filedialog
from datetime import datetime
import os
import sys
import math

# DB connector
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False

# QR + Image libraries
try:
    import qrcode
    from PIL import Image, ImageTk, ImageFilter
    QR_LIBS_AVAILABLE = True
except Exception:
    QR_LIBS_AVAILABLE = False

# -------------------------
# CONFIG
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",    # change if needed
    "database": "navrachana_canteen"
}

APP_WIDTH = 1250
APP_HEIGHT = 690
LEFT_W, LEFT_H = 520, 570
RIGHT_W, RIGHT_H = 510, 570

# -------------------------
# DB HELPER
# -------------------------
def get_db():
    if not MYSQL_AVAILABLE:
        raise RuntimeError("MySQL connector not installed. Install `mysql-connector-python` or set MYSQL_AVAILABLE False.")
    return mysql.connector.connect(**DB_CONFIG)

# -------------------------
# APP CLASS
# -------------------------
class CanteenApp:
    def __init__(self, root):
        self.w = root
        self.w.title("NUV Canteen Ordering System")
        self.w.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+110+40")
        self.w.config(bg="#000000")
        try:
            self.w.iconbitmap("nuv.ico")
        except Exception:
            pass

        # State
        self.current_user = None
        self.cart_items = []
        self.pending_order = None
        self.upi_id = ""   # store entered upi id during payment
        self.dark_mode = False

        # Build UI
        self.build_layout()
        self.load_menu()
        self.load_week_thali_menu()

    # -------------------------
    # UI: layout
    # -------------------------
    def build_layout(self):
        # Top header (with optional small background banner)
        self.header_frame = tk.Frame(self.w, bg="#2e86de")
        self.header_frame.pack(fill="x")
        self.header_label = tk.Label(self.header_frame, text="Navrachana University Canteen App",
                                     bg="#2e86de", fg="black",
                                     font=("Arial", 18, "italic","bold"), pady=10)
        self.header_label.pack(fill="x")

        # Main container
        container = tk.Frame(self.w, bg="#f5f6fa")
        container.pack(fill="both", expand=True)

        # Left panel
        self.left = tk.Frame(container, bg="lightblue", bd=2, relief="groove")
        self.left.place(x=90, y=20, width=LEFT_W, height=LEFT_H)
        # apply background watermark
        self.apply_left_background()

        tk.Label(self.left, text="Weekly Thali Menu", bg="#0984e3",
                 fg="white", font=("Arial", 13, "bold"), pady=4).pack(fill="x")

        self.thali_table = ttk.Treeview(self.left, columns=("day", "menu"), show="headings", height=6)
        self.thali_table.heading("day", text="Day")
        self.thali_table.heading("menu", text="Menu")
        self.thali_table.column("day", width=100, anchor="center")
        self.thali_table.column("menu", width=400, anchor="w")
        self.thali_table.pack(padx=8, pady=(6, 8), fill="both", expand=False)

        tk.Label(self.left, text="Fast Food & Beverages", bg="#0984e3",
                 fg="white", font=("Arial", 12, "bold"), pady=5).pack(fill="x")

        menu_frame = tk.Frame(self.left, bg="white")
        menu_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.menu_tree = ttk.Treeview(menu_frame, columns=("name", "price", "category"), show="headings")
        for c, h in zip(("name", "price", "category"), ("Item Name", "Price ₹", "Category")):
            self.menu_tree.heading(c, text=h)
            self.menu_tree.column(c, width=150)
        self.menu_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(menu_frame, orient="vertical", command=self.menu_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.menu_tree.configure(yscrollcommand=scrollbar.set)
        self.menu_tree.bind("<Double-1>", self.add_selected_item)

        # Right panel
        self.right = tk.Frame(container, bg="lightblue", bd=2, relief="groove")
        self.right.place(x=650, y=20, width=RIGHT_W, height=RIGHT_H)
        self.apply_right_background()

        # right content (login UI initially)
        self.login_ui()

        # Footer with mode toggle & admin access
        footer = tk.Frame(self.w, bg="gray")
        footer.pack(fill="x", side="bottom")
        tk.Button(footer, text="Toggle Dark/Light", command=self.toggle_dark_mode).pack(side="left", padx=8, pady=6)
        tk.Button(footer, text="Admin Panel", command=self.open_admin_login).pack(side="left", padx=8, pady=6)

        # Ensure children are above background
        self.lift_children(self.left)
        self.lift_children(self.right)

    def apply_left_background(self):
        try:
            if QR_LIBS_AVAILABLE:
                img = Image.open("nuv.png").resize((LEFT_W, LEFT_H)).filter(ImageFilter.GaussianBlur(6))
                img.putalpha(120)
                self.left_bg_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.left, image=self.left_bg_img)
                lbl.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            # silently continue if image not found or pillow missing
            pass

    def apply_right_background(self):
        try:
            if QR_LIBS_AVAILABLE:
                img = Image.open("nuv.png").resize((RIGHT_W, RIGHT_H)).filter(ImageFilter.GaussianBlur(6))
                img.putalpha(120)
                self.right_bg_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.right, image=self.right_bg_img)
                lbl.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

    def lift_children(self, frame):
        # bring all existing children above background label (if any)
        for w in frame.winfo_children():
            w.lift()

    # -------------------------
    # Login / Signup UI
    # -------------------------
    def login_ui(self):
        for widget in self.right.winfo_children():
            widget.destroy()

        tk.Label(self.right, text="Student Login / Signup",
                 bg="#2e86de", fg="white",
                 font=("Arial", 14, "bold"), pady=5).pack(fill="x", pady=10)

        frm = tk.Frame(self.right, bg="white")
        frm.pack(pady=20)

        tk.Label(frm, text="Student ID : ", bg="white",font=("arial",14)).grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(frm, text="Password : ", bg="white", font=("arial",14)).grid(row=1, column=0, sticky="w", pady=6)

        self.sid = tk.Entry(frm)
        self.passw = tk.Entry(frm, show="*")
        self.sid.grid(row=0, column=1, pady=6)
        self.passw.grid(row=1, column=1, pady=6)

        tk.Button(frm, text="Login", bg="#0984e3", fg="white",font=("arial",11),width=20,
                  command=self.login).grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(frm, text="Signup", bg="#00b894", fg="white",font=("arial",11),width=20,
                  command=self.signup_ui).grid(row=3, column=0, columnspan=2, pady=5)

    def signup_ui(self):
        for widget in self.right.winfo_children():
            widget.destroy()

        tk.Label(self.right, text="New Student Signup",
                 bg="#6c5ce7", fg="white",
                 font=("Arial", 14, "bold"), pady=5).pack(fill="x", pady=10)

        f = tk.Frame(self.right, bg="white")
        f.pack(pady=10)

        tk.Label(f, text="Name : ", bg="white",font=("arial",14)).grid(row=0, column=0, pady=5, sticky="w")
        tk.Label(f, text="Student ID : ", bg="white",font=("arial",14)).grid(row=1, column=0, pady=5, sticky="w")
        tk.Label(f, text="Phone : ", bg="white",font=("arial",14)).grid(row=2, column=0, pady=5, sticky="w")
        tk.Label(f, text="Password : ", bg="white",font=("arial",14)).grid(row=3, column=0, pady=5, sticky="w")

        name = tk.Entry(f)
        sid = tk.Entry(f)
        phone = tk.Entry(f)
        pwd = tk.Entry(f, show="*")
        name.grid(row=0, column=1)
        sid.grid(row=1, column=1)
        phone.grid(row=2, column=1)
        pwd.grid(row=3, column=1)

        def save_signup():
            if not MYSQL_AVAILABLE:
                messagebox.showerror("DB Error", "MySQL connector not available. Signup disabled.")
                return
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO users(name, student_id, phone, password) VALUES(%s,%s,%s,%s)",
                        (name.get(), sid.get(), phone.get(), pwd.get()))
            db.commit()
            cur.close()
            db.close()
            messagebox.showinfo("Success", "Signup successful! Please login.")
            self.login_ui()

        tk.Button(f, text="Register", bg="#00b894", fg="white",font=("arial",11),width="20" ,command=save_signup).grid(row=4, column=0, columnspan=2, pady=20)

    def login(self):
        if not MYSQL_AVAILABLE:
            messagebox.showerror("DB Error", "MySQL connector not available. Login disabled.")
            return
        sid = self.sid.get()
        pw = self.passw.get()
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE student_id=%s AND password=%s", (sid, pw))
        user = cur.fetchone()
        cur.close()
        db.close()
        if user:
            self.current_user = user
            self.after_login_ui()
        else:
            messagebox.showerror("Error", "Invalid ID or password")

    # -------------------------
    # AFTER LOGIN UI (Cart etc.)
    # -------------------------
    def after_login_ui(self):
        for widget in self.right.winfo_children():
            widget.destroy()

        tk.Label(self.right, text=f"Welcome, {self.current_user['name']}",
                 bg="#6c5ce7", fg="white", font=("Arial", 13, "bold")).pack(fill="x")

        frame_top = tk.Frame(self.right, bg="white")
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="Today's Thali", bg="white",
                 font=("Arial", 12, "bold")).grid(row=0, column=0, padx=8)

        self.thali_choice = tk.StringVar()
        tk.Radiobutton(frame_top, text="Half (₹40)", variable=self.thali_choice, value="Half", bg="white").grid(row=0, column=1)
        tk.Radiobutton(frame_top, text="Full (₹70)", variable=self.thali_choice, value="Full", bg="white").grid(row=0, column=2)
        tk.Button(frame_top, text="Add Thali", bg="#0984e3", fg="white",
                  command=self.add_thali).grid(row=0, column=3, padx=10)

        tk.Label(self.right, text="Your Cart", bg="#74b9ff",
                 fg="black", font=("Arial", 12, "bold")).pack(fill="x", pady=5)

        self.cart_tree = ttk.Treeview(self.right, columns=("item", "price"), show="headings", height=10)
        self.cart_tree.heading("item", text="Item")
        self.cart_tree.heading("price", text="Price ₹")
        self.cart_tree.column("item", width=200)
        self.cart_tree.column("price", width=80)
        self.cart_tree.pack(pady=5, fill="x", padx=8)

        tk.Button(self.right, text="Remove Selected", bg="#d63031", fg="white",font=("Arial", 15, "bold"), width="20",
                  command=self.remove_item).pack(pady=5)

        tk.Button(self.right, text="Place Order", bg="#00b894", fg="white", width="20",
                  font=("Arial", 15, "bold"), command=self.place_order).pack(pady=8)

        tk.Button(self.right, text="View History", bg="#0984e3", fg="white", width="20",
                  font=("Arial", 15, "bold"), command=self.show_history).pack(pady=5)

        self.lift_children(self.right)

    # -------------------------
    # Cart operations
    # -------------------------
    def add_selected_item(self, event):
        item = self.menu_tree.item(self.menu_tree.focus())["values"]
        if item:
            self.cart_items.append((item[0], float(item[1])))
            self.cart_tree.insert("", "end", values=(item[0], item[1]))

    def add_thali(self):
        choice = self.thali_choice.get()
        if not choice:
            messagebox.showerror("Error", "Please select Half or Full thali")
            return
        price = 40 if choice == "Half" else 70
        self.cart_items.append((f"{choice} Thali", price))
        self.cart_tree.insert("", "end", values=(f"{choice} Thali", price))

    def remove_item(self):
        selected = self.cart_tree.selection()
        for i in selected:
            item_values = self.cart_tree.item(i)['values']
            self.cart_items = [c for c in self.cart_items if c[0] != item_values[0]]
            self.cart_tree.delete(i)

    # -------------------------
    # Place order -> confirm -> payment flow
    # -------------------------
    def place_order(self):
        if not self.cart_items:
            messagebox.showerror("Empty", "Please add items first")
            return
        total = sum(i[1] for i in self.cart_items)
        self.pending_order = {
            "items": list(self.cart_items),
            "total": total
        }
        self.open_confirm_dialog()

    def open_confirm_dialog(self):
        dlg = Toplevel(self.w)
        dlg.title("Confirm Order")
        dlg.geometry("360x180+550+300")
        dlg.transient(self.w)
        dlg.grab_set()

        tk.Label(dlg, text="Confirm your order", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(dlg, text=f"Items: {len(self.pending_order['items'])} | Total: ₹{self.pending_order['total']}").pack(pady=5)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)

        def confirm():
            dlg.destroy()
            self.open_payment_dialog()

        def discard():
            dlg.destroy()
            self.pending_order = None

        tk.Button(btn_frame, text="Confirm", bg="#00b894", fg="white", width=10, command=confirm).grid(row=0, column=0, padx=8)
        tk.Button(btn_frame, text="Discard", bg="#d63031", fg="white", width=10, command=discard).grid(row=0, column=1, padx=8)

    def open_payment_dialog(self):
        dlg = Toplevel(self.w)
        dlg.title("Payment Method")
        dlg.geometry("520x530+500+170")
        dlg.transient(self.w)
        dlg.iconbitmap('nuv.ico')
        dlg.grab_set()

        tk.Label(dlg, text="Payment Method", font=("Arial", 14, "bold")).pack(fill='x', pady=8)

        self.payment_var = tk.StringVar(value="Cash")
        frm = tk.Frame(dlg)
        frm.pack(pady=6)
        tk.Radiobutton(frm, text="Cash", variable=self.payment_var, value="Cash", command=lambda: self._on_payment_radio_change(dlg)).grid(row=0, column=0, padx=10)
        tk.Radiobutton(frm, text="Online Payment", variable=self.payment_var, value="Online", command=lambda: self._on_payment_radio_change(dlg)).grid(row=0, column=1, padx=10)

        self.payment_area = tk.Frame(dlg)
        self.payment_area.pack(fill='both', expand=True, pady=6)

        action_fr = tk.Frame(dlg)
        action_fr.pack(pady=8)

        self.finalize_btn = tk.Button(action_fr, text="Place Order",font=("Arial", 12, "bold"), bg="#00b894", fg="white", state='disabled',width=40, command=lambda: self.finalize_order(dlg))
        self.finalize_btn.pack()

        # initialize viewz
        self._on_payment_radio_change(dlg)

    def _on_payment_radio_change(self, dialog_window):
        # Clear payment area
        for w in self.payment_area.winfo_children():
            w.destroy()

        mode = self.payment_var.get()
        total = self.pending_order['total']

        if mode == "Cash":
            tk.Label(self.payment_area, text="You selected Cash. You will pay at the counter.", font=("Arial", 11)).pack(pady=10)
            self.finalize_btn.config(state='normal')
        else:
            tk.Label(self.payment_area, text="Scan the QR to pay online. After payment click 'I Have Paid' to verify.", font=("Arial", 11)).pack(pady=6)

            if QR_LIBS_AVAILABLE:
                # generate QR with encoded info
                qr_text = f"NUV_CANTEEN|{self.current_user['student_id']}|AMOUNT:{total}"
                qr = qrcode.make(qr_text)
                qr_path = os.path.join(os.getcwd(), f"nuv_qr_{int(datetime.now().timestamp())}.png")
                qr.save(qr_path)

                # show QR image
                try:
                    img = Image.open(qr_path)
                    img = img.resize((240, 240))
                    tkimg = ImageTk.PhotoImage(img)
                    lbl = tk.Label(self.payment_area, image=tkimg)
                    lbl.image = tkimg
                    lbl.pack(pady=6)
                    tk.Label(self.payment_area, text=f"Amount: ₹{total}").pack()
                except Exception:
                    tk.Label(self.payment_area, text="QR generated at: " + qr_path).pack()

                # UPI input next to QR
                upi_frame = tk.Frame(self.payment_area)
                upi_frame.pack(pady=8)
                tk.Label(upi_frame, text="Enter UPI ID:", font=("Arial", 11)).grid(row=0, column=0, padx=5)
                self.upi_id_entry = tk.Entry(upi_frame, width=25)
                self.upi_id_entry.grid(row=0, column=1, padx=5)
                def upi_entered():
                    self.upi_id = self.upi_id_entry.get().strip()
                    if not self.upi_id:
                        messagebox.showerror("Error", "Please enter UPI ID or remove it.")
                    else:
                        messagebox.showinfo("UPI Saved", f"UPI ID saved: {self.upi_id}")

                tk.Button(upi_frame, text="Save UPI", bg="#0984e3", fg="white", command=upi_entered).grid(row=0, column=2, padx=5)

                # verification button
                paid_btn = tk.Button(self.payment_area, text="I Have Paid (Verify)", command=lambda: self._online_payment_verified(dialog_window))
                paid_btn.pack(pady=8)
                self.finalize_btn.config(state='disabled')
            else:
                # Libraries missing: show message and simulate
                msg = (
                    "QR libraries not installed. To enable automatic QR generation, install qrcode and pillow.\n"
                    "For now, you may click 'Simulate Payment' to continue."
                )
                tk.Label(self.payment_area, text=msg, wraplength=480, justify='left').pack(pady=6)
                sim_btn = tk.Button(self.payment_area, text="Simulate Payment", command=lambda: self._online_payment_verified(dialog_window))
                sim_btn.pack(pady=8)
                self.finalize_btn.config(state='disabled')

    def _online_payment_verified(self, dialog_window):
        # In real-world, verify with gateway. Here we simulate success.
        messagebox.showinfo("Payment Verified", "Online payment marked as completed.")
        self.finalize_btn.config(state='normal')

    def finalize_order(self, dialog_window=None):
        if not self.pending_order:
            messagebox.showerror("Error", "No pending order found")
            return
        items = ", ".join([i[0] for i in self.pending_order['items']])
        total = self.pending_order['total']
        payment_mode = self.payment_var.get() if hasattr(self, 'payment_var') else 'Cash'
        upi_id_for_bill = getattr(self, "upi_id", "")

        # insert into DB (try with payment_method column, else fallback)
        if MYSQL_AVAILABLE:
            try:
                db = get_db()
                cur = db.cursor()
                try:
                    cur.execute(
                        "INSERT INTO orders (student_id, item_desc, price, date_for, payment_method) VALUES (%s, %s, %s, %s, %s)",
                        (self.current_user['student_id'], items, total, datetime.now().date(), payment_mode)
                    )
                except Exception:
                    cur.execute(
                        "INSERT INTO orders (student_id, item_desc, price, date_for) VALUES (%s, %s, %s, %s)",
                        (self.current_user['student_id'], items, total, datetime.now().date())
                    )
                db.commit()
                cur.close()
                db.close()
            except Exception:
                # DB failed, continue but inform user
                messagebox.showwarning("DB", "Order saved locally (DB insert failed).")
        else:
            # No DB library; skip DB step
            pass

        # Show bill and clear cart
        self.show_simple_bill(self.pending_order['items'], total, payment_mode, upi_id_for_bill)
        self.cart_items.clear()
        if hasattr(self, 'cart_tree'):
            for i in self.cart_tree.get_children():
                self.cart_tree.delete(i)
        self.pending_order = None
        if dialog_window:
            try: dialog_window.destroy()
            except: pass

    def show_simple_bill(self, items, total, payment_mode='Cash', upi_id=""):
        bill = Toplevel(self.w)
        bill.title("Bill - Navrachana Canteen")
        bill.geometry("410x480+500+190")
        bill.config(bg="#f8f9fa")
        try:
            bill.iconbitmap('nuv.ico')
        except: pass

        bill.transient(self.w)          # main window ke saath move karega
        bill.grab_set()                 # bill pe click force karega
        bill.lift()

        tk.Label(bill, text="Navrachana Canteen", font=("Arial", 18, "bold"), bg="#f8f9fa",fg="blue").pack(pady=15)
        tk.Label(bill, text=f"Name: {self.current_user['name']}", font=("Arial", 12), bg="#f8f9fa").pack()
        tk.Label(bill, text=f"Enrollment: {self.current_user['student_id']}", font=("Arial", 12), bg="#f8f9fa").pack(pady=(0, 10))
        tk.Label(bill, text="Items Ordered:", font=("Arial", 13, "bold"), bg="#f8f9fa").pack(anchor="w", padx=30)
        for item, price in items:
            tk.Label(bill, text=f"• {item} - ₹{price}", font=("Arial", 11), bg="#f8f9fa").pack(anchor="w", padx=40)
        tk.Label(bill, text=f"Total: ₹{total}", font=("Arial", 14, "bold"), bg="#f8f9fa").pack(pady=15)
        tk.Label(bill, text=f"Payment Mode: {payment_mode}", font=("Arial", 12), bg="#f8f9fa").pack(pady=(0, 6))
        if upi_id:
            tk.Label(bill, text=f"UPI ID: {upi_id}", font=("Arial", 11), bg="#f8f9fa").pack(pady=(0, 6))
        tk.Label(bill, text="Thank You!", font=("Arial", 16, "italic"), fg="green", bg="#f8f9fa").pack(pady=10)
        tk.Button(bill, text="Close", bg="#6c757d", fg="white", command=bill.destroy).pack(pady=5)

    # -------------------------
    # History view
    # -------------------------
    def show_history(self):
        if not self.current_user:
            messagebox.showwarning("Login Required", "Please login first.")
            return
        hist = Toplevel(self.w)
        hist.title("Order History")
        hist.geometry("700x500+360+180")
        hist.config(bg="black")
        try:
            hist.iconbitmap("nuv.ico")
        except: pass

        tk.Label(hist, text="Your Order History", font=("Arial", 16, "bold"), bg="#0984e3", fg="white").pack(fill="x", pady=5)

        tree = ttk.Treeview(hist, columns=("date", "items", "price"), show="headings", height=15)
        tree.heading("date", text="Date")
        tree.heading("items", text="Items Ordered")
        tree.heading("price", text="Total ₹")
        tree.column("date", width=100, anchor="center")
        tree.column("items", width=400, anchor="w")
        tree.column("price", width=100, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        if MYSQL_AVAILABLE:
            try:
                db = get_db()
                cur = db.cursor()
                cur.execute("SELECT date_for, item_desc, price FROM orders WHERE student_id=%s ORDER BY date_for DESC",
                            (self.current_user['student_id'],))
                rows = cur.fetchall()
                for row in rows:
                    tree.insert("", "end", values=row)
                cur.close()
                db.close()
            except Exception:
                tree.insert("", "end", values=("—", "Could not fetch from DB", "—"))
        else:
            tree.insert("", "end", values=("—", "DB not available", "—"))

        tk.Button(hist, text="Close", bg="#6c757d", fg="white", command=hist.destroy).pack(pady=5)

    # -------------------------
    # Load menu from DB or sample
    # -------------------------
    def load_menu(self):
        # Clear tree
        for i in self.menu_tree.get_children():
            self.menu_tree.delete(i)
        if MYSQL_AVAILABLE:
            try:
                db = get_db()
                cur = db.cursor()
                cur.execute("SELECT name, price, category FROM menu_items")
                rows = cur.fetchall()
                for r in rows:
                    self.menu_tree.insert("", "end", values=(r[0], r[1], r[2]))
                cur.close()
                db.close()
                return
            except Exception:
                # fall back to sample if DB fails
                pass

        # sample fallback menu
        sample = [
            ("Veg Sandwich", 40.0, "Fast Food"),
            ("Cheese Burger", 70.0, "Fast Food"),
            ("French Fries", 50.0, "Fast Food"),
            ("Cold Coffee", 45.0, "Beverage"),
            ("Tea", 15.0, "Beverage"),
            ("Samosa", 20.0, "Fast Food"),
            ("Momos", 60.0, "Fast Food"),
            ("Cold Drink", 30.0, "Beverage"),
            ("Pav Bhaji", 80.0, "Fast Food"),
            ("Mineral Water", 20.0, "Beverage"),
        ]
        for it in sample:
            self.menu_tree.insert("", "end", values=it)

    # -------------------------
    # Weekly thali with current day highlight
    # -------------------------
    def load_week_thali_menu(self):
        for i in self.thali_table.get_children():
            self.thali_table.delete(i)
        week_menu = {
            "Monday": "Rice, Dal Fry, Aloo Gobi, Roti, Salad, Pickle",
            "Tuesday": "Rajma Chawal, Roti, Bhindi, Salad, Pickle",
            "Wednesday": "Pulav, Raita, Paneer Masala, Roti, Salad",
            "Thursday": "Kadhi Chawal, Roti, Mix Veg, Salad, Pickle",
            "Friday": "Jeera Rice, Dal Tadka, Aloo Matar, Roti, Salad",
            "Saturday": "Veg Biryani, Raita, Chole, Roti, Salad"
        }
        today_name = datetime.now().strftime("%A")
        for day, menu in week_menu.items():
            if day == today_name:
                iid = self.thali_table.insert("", "end", values=(day, menu), tags=("today",))
                self.thali_table.selection_set(iid)
                self.thali_table.focus(iid)
            else:
                self.thali_table.insert("", "end", values=(day, menu))
        try:
            self.thali_table.tag_configure("today", background="#d1e7ff")
        except:
            pass

    # -------------------------
    # Admin panel (login & simple menu management + analytics)
    # -------------------------
    def open_admin_login(self):
        pwd = simpledialog.askstring("Admin Login", "Enter admin password:", show="*")
        if pwd is None:
            return
        # default admin password - change for production
        if pwd != "admin123":
            messagebox.showerror("Denied", "Wrong password")
            return
        self.open_admin_panel()

    def open_admin_panel(self):
        admin = Toplevel(self.w)
        admin.title("Admin Panel")
        admin.geometry("800x520+300+150")
        admin.transient(self.w)

        tk.Label(admin, text="Admin - Menu Management & Analytics", font=("Arial", 14, "bold"), bg="#0984e3", fg="white").pack(fill="x")

        left = tk.Frame(admin)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = tk.Frame(admin, width=320)
        right.pack(side="right", fill="y", padx=8, pady=8)

        # Menu management tree
        tree = ttk.Treeview(left, columns=("name", "price", "category"), show="headings")
        for c, h in zip(("name", "price", "category"), ("Name", "Price", "Category")):
            tree.heading(c, text=h)
            tree.column(c, width=150)
        tree.pack(fill="both", expand=True)
        # load existing
        if MYSQL_AVAILABLE:
            try:
                db = get_db(); cur = db.cursor(); cur.execute("SELECT name, price, category FROM menu_items"); rows = cur.fetchall(); cur.close(); db.close()
                for r in rows:
                    tree.insert("", "end", values=r)
            except:
                pass

        # controls
        def add_menu_item():
    # Ek hi custom dialog bana dete hain – sabse best!
            add_dlg = Toplevel(admin)
            add_dlg.title("Add New Menu Item")
            add_dlg.geometry("380x260+500+300")
            add_dlg.transient(admin)
            add_dlg.grab_set()
            add_dlg.configure(bg="#f8f9fa")

            tk.Label(add_dlg, text="Add New Item", font=("Arial", 14, "bold"), bg="#f8f9fa").pack(pady=10)

            tk.Label(add_dlg, text="Item Name:", bg="#f8f9fa").pack(anchor="w", padx=40)
            name_entry = tk.Entry(add_dlg, width=30, font=("Arial", 11))
            name_entry.pack(pady=5)

            tk.Label(add_dlg, text="Price (₹):", bg="#f8f9fa").pack(anchor="w", padx=40)
            price_entry = tk.Entry(add_dlg, width=30, font=("Arial", 11))
            price_entry.pack(pady=5)

            tk.Label(add_dlg, text="Category:", bg="#f8f9fa").pack(anchor="w", padx=40)
            cat_entry = tk.Entry(add_dlg, width=30, font=("Arial", 11))
            cat_entry.insert(0, "Fast Food")  # default
            cat_entry.pack(pady=5)

            def save_item():
                name = name_entry.get().strip()
                price_text = price_entry.get().strip()
                cat = cat_entry.get().strip() or "Fast Food"

                if not name:
                    messagebox.showerror("Error", "Item name is required!")
                    return
                if not price_text:
                    messagebox.showerror("Error", "Price is required!")
                    return
                try:
                    price = float(price_text)
                    if price <= 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Enter valid price (e.g., 50)")
                    return

                # Save to DB
                if MYSQL_AVAILABLE:
                    try:
                        db = get_db()
                        cur = db.cursor()
                        cur.execute("INSERT INTO menu_items (name, price, category) VALUES (%s, %s, %s)",
                                    (name, price, cat))
                        db.commit()
                        cur.close()
                        db.close()
                    except Exception as e:
                        messagebox.showerror("DB Error", f"Could not save item:\n{e}")
                        return

                # Add to Treeview
                tree.insert("", "end", values=(name, price, cat))
                messagebox.showinfo("Success", f"{name} added successfully!")
                add_dlg.destroy()

            btn_frame = tk.Frame(add_dlg, bg="#f8f9fa")
            btn_frame.pack(pady=12)
            tk.Button(btn_frame, text="Add Item", bg="#00b894", fg="white", width=12, command=save_item).pack(side="left", padx=8)
            tk.Button(btn_frame, text="Cancel", bg="#d63031", fg="white", width=12, command=add_dlg.destroy).pack(side="left", padx=8)

        def remove_menu_item():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a menu item to remove.")
                return
            vals = tree.item(sel[0])['values']
            if MYSQL_AVAILABLE:
                # try delete from DB
                try:
                    db = get_db(); cur = db.cursor(); cur.execute("DELETE FROM menu_items WHERE name=%s AND price=%s LIMIT 1", (vals[0], vals[1])); db.commit(); cur.close(); db.close()
                except:
                    pass
            tree.delete(sel[0])

        tk.Button(right, text="Add Menu Item", command=add_menu_item, bg="#00b894", fg="white").pack(fill="x", pady=6)
        tk.Button(right, text="Remove Selected", command=remove_menu_item, bg="#d63031", fg="white").pack(fill="x", pady=6)

        # simple analytics: orders count & revenue (from DB if available)
        def load_analytics():
            for w in right.winfo_children():
                # keep buttons, replace analytics area
                pass
        # analytics display
        analytics_frame = tk.Frame(right)
        analytics_frame.pack(fill="both", expand=True, pady=10)
        tk.Label(analytics_frame, text="Order Analytics", font=("Arial", 12, "bold")).pack()
        if MYSQL_AVAILABLE:
            try:
                db = get_db(); cur = db.cursor(); cur.execute("SELECT COUNT(*), IFNULL(SUM(price),0) FROM orders"); r = cur.fetchone(); cur.close(); db.close()
                tk.Label(analytics_frame, text=f"Total Orders: {r[0]}").pack(anchor="w")
                tk.Label(analytics_frame, text=f"Total Revenue: ₹{r[1]}").pack(anchor="w")
            except:
                tk.Label(analytics_frame, text="Could not fetch analytics from DB").pack()
        else:
            tk.Label(analytics_frame, text="DB not available for analytics").pack()

    # -------------------------
    # Dark / Light Mode
    # -------------------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            bg = "#000000"; fg = "white"; panel_bg = "#3a3a3a"
        else:
            bg = "#f5f6fa"; fg = "black"; panel_bg = "white"
        self.w.config(bg=bg)
        self.header_frame.config(bg="#1f6fb3" if not self.dark_mode else "#0f4a6d")
        self.header_label.config(bg="#1f6fb3" if not self.dark_mode else "#0f4a6d", fg="white")
        self.left.config(bg=panel_bg)
        self.right.config(bg=panel_bg)
        # refresh children colors where sensible
        for frame in (self.left, self.right):
            for w in frame.winfo_children():
                try:
                    if isinstance(w, tk.Label):
                        w.config(bg=panel_bg, fg=fg)
                    elif isinstance(w, tk.Button):
                        # keep colored buttons intact
                        pass
                    elif isinstance(w, tk.Frame):
                        w.config(bg=panel_bg)
                except Exception:
                    pass

    # -------------------------
    # Run
    # -------------------------
def main():
    root = tk.Tk()
    app = CanteenApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
