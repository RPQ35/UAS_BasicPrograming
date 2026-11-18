

import tkinter as tk

minus_color="#d64545"
Plus_color="#2e9e4f"
font_color="#fdfdfd" 

# # ==============================================================
# #               Menu data 
# # ==============================================================
MENU = {
    "Gorengan": [("Bakwan", 2000), ("Tahu Isi", 3000),
                 ("Tempe Goreng", 2500), ("Pisang Goreng", 4000)],
    "Minuman":  [("Teh Manis", 3000), ("Es Jeruk", 5000), ("Kopi", 4000)],
}

# ----------------  order VARIABLE ----------------
# order = [ [index, category, name, ordered number], ... ]
order = []
price_of = {}      # name -> price, kept aside so 'order' stays exactly as requested

i = 0
for category, items in MENU.items():
    for name, price in items:
        price_of[name] = price
        order.append([i, category, name, 0])
        i += 1


# ---------------- Oredered menu LOGIC ----------------
def add(index):
    order[index][3] += 1          # goes up, so always >= 1
    refresh()


def sub(index):
    if order[index][3] > 0:       # validate: never below 0
        order[index][3] -= 1
    refresh()


def rupiah(n):
    return "Rp " + "{:,}".format(n).replace(",", ".")



# # ==============================================================
# #               ordered menu list
# # ==============================================================
# ---------------- DRAWING ----------------
def refresh():
    # clear panels when new order is added
    for w in menu_body.winfo_children():
        w.destroy()
    for w in order_body.winfo_children():
        w.destroy()

    # LEFT PANEL: full menu
    for category in MENU:
        tk.Label(menu_body, text=category, bg="#333333", fg="white",
                 font=("Georgia", 11, "bold"), anchor="w").pack(fill="x", padx=8, pady=(8, 4))
        for row in order:
            if row[1] == category:
                draw_menu_row(row)

    # RIGHT PANEL: Ordered menu
    for row in order:
        if row[3] > 0:
            draw_order_row(row)

    if not any(row[3] > 0 for row in order):
        tk.Label(order_body, text="Belum ada pesanan", bg="white",
                 fg="#999999", font=("Georgia", 10)).pack(pady=30)

    # total
    total = sum(row[3] * price_of[row[2]] for row in order)
    total_label.config(text="TOTAL  " + rupiah(total))

    

# ------main function to draw each menu row
def draw_menu_row(row):
    index, category, name, qty = row
    f = tk.Frame(menu_body, bg=font_color, bd=1, relief="solid")
    f.pack(fill="x", padx=8, pady=3)

    tk.Label(f, text=name, bg=font_color, anchor="w",#menu name
             font=("Georgia", 11)).grid(row=0, column=0, sticky="w", padx=8, pady=6)
    
    tk.Label(f, text=rupiah(price_of[name]), bg=font_color, width=11,#price tag
             font=("Georgia", 10)).grid(row=0, column=1, padx=4)
    
    # multiplyed number / ordered number
    tk.Label(f, text="x " + str(qty), bg=font_color, width=4,
             font=("Georgia", 10, "bold")).grid(row=0, column=2, padx=4)
    
    #button
    tk.Button(f, text="+", width=3, bg=Plus_color, fg="white", activebackground="#257a3d",
              command=lambda i=index: add(i)).grid(row=0, column=3, padx=(4, 8))

    f.columnconfigure(0, weight=1)

# ------ function to draw each ordered menu
def draw_order_row(row):
    index, category, name, qty = row
    f = tk.Frame(order_body, bg=font_color, bd=1, relief="solid")
    f.pack(fill="x", padx=8, pady=3)

    # menu name
    tk.Label(f, text=name, bg=font_color, anchor="w",
             font=("Georgia", 11)).grid(row=0, column=0, sticky="w", padx=8, pady=6)
    
    # multiplyed number / ordered number
    tk.Label(f, text="x " + str(qty), bg=font_color, width=4,
             font=("Georgia", 10, "bold")).grid(row=0, column=1, padx=4)
    
    #button
    tk.Button(f, text="-", width=3, bg=minus_color, fg="white", activebackground="#b23636",
              command=lambda i=index: sub(i)).grid(row=0, column=2, padx=3)
    tk.Button(f, text="+", width=3, bg=Plus_color, fg="white", activebackground="#257a3d",
              command=lambda i=index: add(i)).grid(row=0, column=3, padx=(3, 8))

    f.columnconfigure(0, weight=1)


# # ==============================================================
# #               main window 
# # ==============================================================
root = tk.Tk()
root.title("Warung Sederhana")
root.geometry("900x560")
root.configure(bg="#eeeeee")

tk.Label(root, text="WARUNG SEDERHANA", bg="#2b2b2b", fg="#ffd24d",
         font=("Georgia", 20, "bold"), pady=16).pack(fill="x")

body = tk.Frame(root, bg="#eeeeee")
body.pack(fill="both", expand=True, padx=12, pady=12)
body.columnconfigure(0, weight=1)
body.columnconfigure(1, weight=1)
body.rowconfigure(0, weight=1)

menu_panel = tk.Frame(body, bg="white", bd=2, relief="ridge")
menu_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

order_panel = tk.Frame(body, bg="white", bd=2, relief="ridge")
order_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

tk.Label(menu_panel, text="Menu", bg="white",
         font=("Georgia", 14, "bold")).pack(pady=(10, 4))
tk.Label(order_panel, text="Ordered Menu", bg="white",
         font=("Georgia", 14, "bold")).pack(pady=(10, 4))

menu_body = tk.Frame(menu_panel, bg="white")
menu_body.pack(fill="both", expand=True)

order_body = tk.Frame(order_panel, bg="white")
order_body.pack(fill="both", expand=True)

total_label = tk.Label(order_panel, text="TOTAL  Rp 0", bg="#2b2b2b", fg="#ffd24d",
                       font=("Georgia", 12, "bold"), pady=10)
total_label.pack(fill="x", side="bottom")

refresh()
root.mainloop()