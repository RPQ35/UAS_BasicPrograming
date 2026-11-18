import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import hashlib
import mysql.connector

# ---------------- SETTING ----------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "live"                # <- isi password mysql 
DB_NAME = "warung_db"

ADMIN_PASSWORD = "admin123"  # <- password admin panel & reset database

DATA_AWAL = [
    ("Gorengan", "Bakwan", 2000),
    ("Gorengan", "Tahu Isi", 3000),
    ("Gorengan", "Tempe Goreng", 2500),
    ("Minuman", "Teh Manis", 3000),
    ("Minuman", "Es Jeruk", 5000),
]

# ---------------- THE order VARIABLE ----------------
order = []          # [ [index, type, name, qty], ... ]
price_of = {}       # name -> price
id_of = {}          # name -> menu id


# ============ PASSWORD ============
def cek_password():
    pw = simpledialog.askstring("Password", "Masukkan password admin:",
                                show="*", parent=root)
    if pw == ADMIN_PASSWORD:
        return True
    messagebox.showerror("Salah", "Password salah!")
    return False


# ============ 1. KONEKSI ============
def get_conn(with_db=True):
    try:
        if with_db:
            return mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        return mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS)
    except mysql.connector.Error as e:
        messagebox.showerror("Koneksi Gagal", str(e))
        return None


# ============ 2. BUAT DATABASE (OTOMATIS SAAT DIBUKA) ============
def buat_database_jika_belum_ada():
    conn = get_conn(with_db=False)
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.database = DB_NAME
        cur.execute("""CREATE TABLE IF NOT EXISTS menu (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        type VARCHAR(50), name VARCHAR(100), price INT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS checkout (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        total INT, created_at DATETIME)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS checkout_detail (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        checkout_id INT UNIQUE, 
                        menu_id INT UNIQUE, 
                        qty INT,
                        subtotal INT,
                    
                        CONSTRAINT fk_menu FOREIGN KEY (menu_id) REFERENCES menu(id) ON DELETE RESTRICT ON UPDATE CASCADE,
                        CONSTRAINT fk_checkout FOREIGN KEY (Checkout_id) REFERENCES checkout(id) ON DELETE RESTRICT ON UPDATE CASCADE
                    )""")
        cur.execute("SELECT COUNT(*) FROM menu")
        if cur.fetchone()[0] == 0:
            for t, n, p in DATA_AWAL:
                cur.execute("INSERT INTO menu (type,name,price) VALUES (%s,%s,%s)",
                            (t, n, p))
        conn.commit()
    except mysql.connector.Error as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()


# ============ 3. RESET DATABASE (admin only ) ============
def reset_database():
    if not cek_password():
        return
    if not messagebox.askyesno(
            "PERINGATAN !!!",
            "Semua data (menu + transaksi) akan DIHAPUS PERMANEN.\n"
            "Database akan dibuat ulang dari awal.\n\nLanjutkan?"):
        return
    if not messagebox.askyesno("KONFIRMASI TERAKHIR",
                               "Benar-benar yakin? Tidak bisa dibatalkan."):
        return

    conn = get_conn(with_db=False)
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        conn.commit()
        conn.close()
        buat_database_jika_belum_ada()
        load_menu()
        messagebox.showinfo("Sukses", "Database berhasil dibuat ulang.")
    except mysql.connector.Error as e:
        messagebox.showerror("Error", str(e))


# ============ 4. AMBIL MENU DARI MYSQL ============
def load_menu():
    global order
    order = []
    price_of.clear()
    id_of.clear()
    conn = get_conn()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id,type,name,price FROM menu ORDER BY type, name")
        for i, (mid, tipe, nama, harga) in enumerate(cur.fetchall()):
            price_of[nama] = harga
            id_of[nama] = mid
            order.append([i, tipe, nama, 0])
    except mysql.connector.Error as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()
    refresh()


# ============ 5. LOGIC PLUS / MINUS ============
def tambah(index):
    order[index][3] += 1
    refresh()


def kurang(index):
    if order[index][3] > 0:          # validasi: tidak boleh kurang dari 0
        order[index][3] -= 1
    refresh()


def rupiah(n):
    return "Rp " + "{:,}".format(n).replace(",", ".")


def hash_id(checkout_id):
    h = hashlib.md5(str(checkout_id).encode()).digest()
    huruf = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(huruf[b % 36] for b in h[:4])


# ============ 6. GAMBAR ULANG LAYAR ============
def refresh():
    for w in menu_body.winfo_children():
        w.destroy()
    for w in order_body.winfo_children():
        w.destroy()

    tipe_sekarang = ""
    for row in order:
        if row[1] != tipe_sekarang:
            tipe_sekarang = row[1]
            tk.Label(menu_body, text=tipe_sekarang, bg="#333333", fg="white",
                     font=("Georgia", 11, "bold"), anchor="w").pack(fill="x", padx=8, pady=(8, 4))
        gambar_menu(row)

    for row in order:
        if row[3] > 0:
            gambar_ordered(row)

    if not any(row[3] > 0 for row in order):
        tk.Label(order_body, text="Belum ada pesanan", bg="white",
                 fg="#999999", font=("Georgia", 10)).pack(pady=30)

    total = sum(row[3] * price_of[row[2]] for row in order)
    total_label.config(text="TOTAL  " + rupiah(total))


def gambar_menu(row):
    index, tipe, nama, qty = row
    f = tk.Frame(menu_body, bg="#fdfdfd", bd=1, relief="solid")
    f.pack(fill="x", padx=8, pady=3)
    tk.Label(f, text=nama, bg="#fdfdfd", anchor="w",
             font=("Georgia", 11)).grid(row=0, column=0, sticky="w", padx=8, pady=6)
    tk.Label(f, text=rupiah(price_of[nama]), bg="#fdfdfd", width=11,
             font=("Georgia", 10)).grid(row=0, column=1, padx=4)
    tk.Label(f, text="x " + str(qty), bg="#fdfdfd", width=4,
             font=("Georgia", 10, "bold")).grid(row=0, column=2, padx=4)
    tk.Button(f, text="+", width=3, bg="#2e9e4f", fg="white",
              command=lambda i=index: tambah(i)).grid(row=0, column=3, padx=(4, 8))
    f.columnconfigure(0, weight=1)


def gambar_ordered(row):
    index, tipe, nama, qty = row
    f = tk.Frame(order_body, bg="#fdfdfd", bd=1, relief="solid")
    f.pack(fill="x", padx=8, pady=3)
    tk.Label(f, text=nama, bg="#fdfdfd", anchor="w",
             font=("Georgia", 11)).grid(row=0, column=0, sticky="w", padx=8, pady=6)
    tk.Label(f, text="x " + str(qty), bg="#fdfdfd", width=4,
             font=("Georgia", 10, "bold")).grid(row=0, column=1, padx=4)
    tk.Button(f, text="-", width=3, bg="#d64545", fg="white",
              command=lambda i=index: kurang(i)).grid(row=0, column=2, padx=3)
    tk.Button(f, text="+", width=3, bg="#2e9e4f", fg="white",
              command=lambda i=index: tambah(i)).grid(row=0, column=3, padx=(3, 8))
    f.columnconfigure(0, weight=1)


# ============ 7. CHECKOUT -> SIMPAN KE MYSQL ============
def checkout():
    items = [r for r in order if r[3] > 0]
    if not items:
        messagebox.showwarning("Kosong", "Belum ada pesanan.")
        return

    total = sum(r[3] * price_of[r[2]] for r in items)
    conn = get_conn()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO checkout (total, created_at) VALUES (%s,%s)",
                    (total, datetime.now()))
        checkout_id = cur.lastrowid
        for r in items:
            cur.execute("""INSERT INTO checkout_detail
                           (checkout_id, menu_id, qty, subtotal) VALUES (%s,%s,%s,%s)""",
                        (checkout_id, id_of[r[2]], r[3], r[3] * price_of[r[2]]))
        conn.commit()
        for r in order:
            r[3] = 0
        refresh()
        messagebox.showinfo("Sukses",
                            f"Pesanan disimpan.\nID: {hash_id(checkout_id)}\n"
                            f"Total: {rupiah(total)}")
    except mysql.connector.Error as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()


# ============ 8. ADMIN PANEL ============
def admin_panel():
    if not cek_password():
        return

    win = tk.Toplevel(root)
    win.title("Admin Panel")
    win.geometry("820x600")
    win.configure(bg="#eeeeee")

    tk.Label(win, text="ADMIN PANEL", bg="#2b2b2b", fg="#ffd24d",
             font=("Georgia", 16, "bold"), pady=10).pack(fill="x")

    tab = ttk.Notebook(win)
    tab.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- TAB 1: CRUD MENU ----------
    tab_menu = tk.Frame(tab, bg="#eeeeee")
    tab.add(tab_menu, text="  Menu CRUD  ")

    form = tk.Frame(tab_menu, bg="#eeeeee")
    form.pack(pady=10)

    tk.Label(form, text="Type", bg="#eeeeee").grid(row=0, column=0, sticky="w")
    e_type = tk.Entry(form, width=15)
    e_type.grid(row=1, column=0, padx=5)

    tk.Label(form, text="Name", bg="#eeeeee").grid(row=0, column=1, sticky="w")
    e_name = tk.Entry(form, width=22)
    e_name.grid(row=1, column=1, padx=5)

    tk.Label(form, text="Price", bg="#eeeeee").grid(row=0, column=2, sticky="w")
    e_price = tk.Entry(form, width=10)
    e_price.grid(row=1, column=2, padx=5)

    kolom = ("id", "type", "name", "price")
    tree = ttk.Treeview(tab_menu, columns=kolom, show="headings", height=13)
    for c, w in zip(kolom, (40, 120, 240, 100)):
        tree.heading(c, text=c.upper())
        tree.column(c, width=w, anchor="w")
    tree.pack(padx=12, pady=6, fill="both", expand=True)

    def isi_tabel():
        for i in tree.get_children():
            tree.delete(i)
        conn = get_conn()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT id,type,name,price FROM menu ORDER BY type,name")
            for row in cur.fetchall():
                tree.insert("", "end", values=row)
        finally:
            conn.close()

    def pilih(event):
        if not tree.selection():
            return
        v = tree.item(tree.selection()[0], "values")
        e_type.delete(0, "end"); e_type.insert(0, v[1])
        e_name.delete(0, "end"); e_name.insert(0, v[2])
        e_price.delete(0, "end"); e_price.insert(0, v[3])

    tree.bind("<<TreeviewSelect>>", pilih)

    def tambah_menu():
        if e_name.get() == "" or e_price.get() == "":
            messagebox.showwarning("Kosong", "Name dan Price wajib diisi.")
            return
        try:
            harga = int(e_price.get())
        except ValueError:
            messagebox.showerror("Error", "Price harus angka.")
            return
        conn = get_conn()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO menu (type,name,price) VALUES (%s,%s,%s)",
                        (e_type.get(), e_name.get(), harga))
            conn.commit()
            isi_tabel()
            load_menu()
        finally:
            conn.close()

    def ubah_menu():
        if not tree.selection():
            messagebox.showwarning("Pilih", "Pilih data dulu di tabel.")
            return
        try:
            harga = int(e_price.get())
        except ValueError:
            messagebox.showerror("Error", "Price harus angka.")
            return
        mid = tree.item(tree.selection()[0], "values")[0]
        conn = get_conn()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("UPDATE menu SET type=%s,name=%s,price=%s WHERE id=%s",
                        (e_type.get(), e_name.get(), harga, mid))
            conn.commit()
            isi_tabel()
            load_menu()
        finally:
            conn.close()

    def hapus_menu():
        if not tree.selection():
            messagebox.showwarning("Pilih", "Pilih data dulu di tabel.")
            return
        if not messagebox.askyesno("Hapus", "Hapus menu ini?"):
            return
        mid = tree.item(tree.selection()[0], "values")[0]
        conn = get_conn()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM menu WHERE id=%s", (mid,))
            conn.commit()
            isi_tabel()
            load_menu()
        finally:
            conn.close()

    tombol = tk.Frame(tab_menu, bg="#eeeeee")
    tombol.pack(pady=8)
    tk.Button(tombol, text="ADD", width=12, bg="#2e9e4f", fg="white",
              command=tambah_menu).pack(side="left", padx=5)
    tk.Button(tombol, text="UPDATE", width=12, bg="#2b6cb0", fg="white",
              command=ubah_menu).pack(side="left", padx=5)
    tk.Button(tombol, text="DELETE", width=12, bg="#d64545", fg="white",
              command=hapus_menu).pack(side="left", padx=5)
    tk.Button(tombol, text="REFRESH", width=12,
              command=isi_tabel).pack(side="left", padx=5)

    isi_tabel()

    # ---------- TAB 2: CHECKOUT HISTORY ----------
    tab_hist = tk.Frame(tab, bg="#eeeeee")
    tab.add(tab_hist, text="  Checkout History  ")

    kol = ("no", "date", "checkout_id", "ordered_menu", "qty", "subtotal", "total")
    hist = ttk.Treeview(tab_hist, columns=kol, show="headings", height=18)
    for c, w in zip(kol, (35, 95, 110, 190, 45, 90, 100)):
        hist.heading(c, text=c.upper())
        hist.column(c, width=w, anchor="w")
    hist.tag_configure("total", background="#ffe9a8", font=("Georgia", 9, "bold"))
    hist.pack(padx=10, pady=10, fill="both", expand=True)

    def isi_history():
        for i in hist.get_children():
            hist.delete(i)
        conn = get_conn()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("""SELECT c.id, c.created_at, c.total,
                                  COALESCE(m.name,'(terhapus)'), d.qty, d.subtotal
                           FROM checkout c
                           JOIN checkout_detail d ON d.checkout_id = c.id
                           LEFT JOIN menu m ON m.id = d.menu_id
                           ORDER BY c.id DESC, d.id""")
            rows = cur.fetchall()

            # kelompokkan per checkout_id
            grup = {}
            urutan = []
            for cid, tgl, total, nama, qty, sub in rows:
                if cid not in grup:
                    grup[cid] = {"tgl": tgl, "total": total, "items": []}
                    urutan.append(cid)
                grup[cid]["items"].append((nama, qty, sub))

            for no, cid in enumerate(urutan, 1):
                g = grup[cid]
                tgl = g["tgl"].strftime("%d/%m/%Y")
                code = hash_id(cid)
                for i, (nama, qty, sub) in enumerate(g["items"]):
                    hist.insert("", "end", values=(
                        no if i == 0 else "",
                        tgl if i == 0 else "",
                        code if i == 0 else "",
                        nama, qty, rupiah(sub), ""))
                # baris total di akhir grup
                hist.insert("", "end", values=(
                    "", "", "", "", "", "", rupiah(g["total"])), tags=("total",))
        finally:
            conn.close()

    tk.Button(tab_hist, text="REFRESH HISTORY", width=18,
              command=isi_history).pack(pady=(0, 10))

    isi_history()

    # ---------- TOMBOL RESET (HANYA DI ADMIN) ----------
    tk.Button(win, text="RESET / BUAT ULANG DATABASE", bg="#d64545", fg="white",
              font=("Georgia", 10, "bold"), pady=6,
              command=lambda: [reset_database(), isi_tabel(), isi_history()]
              ).pack(fill="x", padx=10, pady=(0, 12))


# ============ 9. WINDOW UTAMA ============
root = tk.Tk()
root.title("Warung Sederhana - MySQL")
root.geometry("960x620")
root.configure(bg="#eeeeee")

head = tk.Frame(root, bg="#2b2b2b")
head.pack(fill="x")
tk.Label(head, text="WARUNG SEDERHANA", bg="#2b2b2b", fg="#ffd24d",
         font=("Georgia", 18, "bold")).pack(side="left", padx=14, pady=12)
tk.Button(head, text="ADMIN", bg="#2b6cb0", fg="white",
          command=admin_panel).pack(side="right", padx=10, pady=10)

body = tk.Frame(root, bg="#eeeeee")
body.pack(fill="both", expand=True, padx=12, pady=12)
body.columnconfigure(0, weight=1)
body.columnconfigure(1, weight=1)
body.rowconfigure(0, weight=1)

menu_panel = tk.Frame(body, bg="white", bd=2, relief="ridge")
menu_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
order_panel = tk.Frame(body, bg="white", bd=2, relief="ridge")
order_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

tk.Label(menu_panel, text="Menu (dari MySQL)", bg="white",
         font=("Georgia", 13, "bold")).pack(pady=(10, 4))
tk.Label(order_panel, text="Ordered Menu", bg="white",
         font=("Georgia", 13, "bold")).pack(pady=(10, 4))

menu_body = tk.Frame(menu_panel, bg="white")
menu_body.pack(fill="both", expand=True)
order_body = tk.Frame(order_panel, bg="white")
order_body.pack(fill="both", expand=True)

# total + checkout di bawah panel ordered
total_label = tk.Label(order_panel, text="TOTAL  Rp 0", bg="#2b2b2b", fg="#ffd24d",
                       font=("Georgia", 12, "bold"), pady=10)
total_label.pack(fill="x", side="bottom")

tk.Button(order_panel, text="CHECKOUT", bg="#2e9e4f", fg="white",
          font=("Georgia", 12, "bold"), pady=8,
          command=checkout).pack(fill="x", side="bottom")

# jalankan saat program dibuka
buat_database_jika_belum_ada()
load_menu()
root.mainloop()