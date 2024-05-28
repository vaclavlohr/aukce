import tkinter as tk
from tkinter import ttk
from gpiozero import Button
from time import sleep, time
import threading
import numpy as np
import sys

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

from gpiozero import LED
import time

# Nastavení LED pinů
led_pins = [5, 6, 13, 19, 26]

# Vytvoření seznamu objektů LED
leds = [LED(pin) for pin in led_pins]

def led_on(index):
    """ Zapne LED podle zadaného indexu. """
    leds[index].on()

def led_off(index):
    """ Vypne LED podle zadaného indexu. """
    leds[index].off()

def all_leds_on():
    """ Zapne všechny LED. """
    for led in leds:
        led.on()

def all_leds_off():
    """ Vypne všechny LED. """
    for led in leds:
        led.off()

def test_leds():
    """ Testovací funkce pro zapnutí a vypnutí všech LED. """
    all_leds_on()
    time.sleep(2)  # Pauza, aby byly LED viditelně zapnuté
    all_leds_off()

# Globální proměnné
num_players = 5
num_auctions = 10  # Počet aukcí
current_auction = 0  # Aktuální počet provedených aukcí
buttons = [Button(2), Button(3), Button(4), Button(17), Button(27)]
scores = [0] * num_players
win_rounds = [0] * num_players
current_price = 1000
registered_players = [False] * num_players
registration_time_limit = 10  # čas na přihlášení v sekundách
auction_active = False
registration_active = True  # Inicializace stavu registrace
auction_countdown = False

registration_updated = False
scores_updated = False
update_labels = False
price_label_text = ""
round_label_text = ""
countdown_label_text = ""


# Celkový součet
total_sum = 5000

# Vygenerování náhodných hodnot
random_values = np.random.rand(num_auctions)
# Normalizace hodnot tak, aby jejich součet byl roven 1
normalized_values = random_values / random_values.sum()
# Vynásobení normalizovaných hodnot celkovým součtem
scaled_values = normalized_values * total_sum

# Zaokrouhlení na celé číslo
final_values = np.round(scaled_values).astype(int)

# Úprava pro zajištění přesného součtu 10000
difference = total_sum - final_values.sum()
indices = np.random.choice(np.arange(num_auctions), size=abs(difference), replace=True)
if difference > 0:
    final_values[indices] += 1
else:
    final_values[indices] -= 1

print(final_values)
print("Součet hodnot:", final_values.sum())


def countdown_timer(count, action):
    global countdown_label_text, update_labels
    for i in range(count, 0, -1):
        countdown_label_text = f"{action} za {i} sekund."
        update_labels = True
        update_window()
        sleep(1)
    countdown_label_text = ""
    update_labels = True
    update_window()

def run_auction():
    global current_price, auction_active, current_auction, final_values, auction_countdown
    global price_label_text, round_label_text, countdown_label_text, update_labels
    #current_price = 1000
    current_price = final_values[current_auction]
    bid_decrement = np.random.randint(2, 11)
    registration_active = False

    #countdown_timer(5, "auction round")  # 5 sekundový odpočet před začátkem aukce

    price_label_text=f"Startovní cena: {current_price}\n"
    round_label_text=f"Kolo aukce #{current_auction+1} z {num_auctions}"
    update_labels = True
    draw_gauge(current_price)
    update_window()

    if (not auction_countdown): 
        auction_countdown = True

        countdown_timer(5, f"{current_auction+1}. kolo aukce začne")  # 5 sekundový odpočet před začátkem aukce

        auction_countdown = False
        auction_active = True

        while auction_active and current_price > 0:
            current_price -= bid_decrement
            price_label_text=f"Cena: {current_price}\n"
            update_labels = True
            draw_gauge(current_price)
            update_window()
            #sleep(0.01)  # Zkrácený čas pro dynamickou aukci

        if auction_active:
            handle_auction_end(-1) #No winner

def evaluate_winner(final):
    global price_label_text, round_label_text, countdown_label_text, update_labels
    max_wins = -1
    min_score = float('inf')
    winner_index = -1
    
    # Procházení každého hráče a hledání vítěze
    for i in range(num_players):
        wins = win_rounds[i]
        score = scores[i]
        
        # Kontrola, zda má hráč více výher, nebo stejný počet výher ale nižší skóre
        if wins > max_wins or (wins == max_wins and score < min_score):
            max_wins = wins
            min_score = score
            winner_index = i

    # Aktualizace labelu s informací o vítězi
    if (final == False):
        round_label_text=f"Průběžným vítězem aukce je: Hráč {winner_index + 1} s {win_rounds[winner_index]} výhrami a skóre {scores[winner_index]}"
    if (final == True):
        round_label_text=f"Celkovým vítězem aukce je: Hráč {winner_index + 1} s {win_rounds[winner_index]} výhrami a skóre {scores[winner_index]}"
    update_labels = True
    
    # Zvýraznění vítěze v Treeview
    for child in tree.get_children():
        tree.item(child, tags=('normal',))  # Resetování všech značek
    tree.item(tree.get_children()[winner_index], tags=('winner',))
    
    update_window()

def handle_auction_end(winner):
    global current_auction, auction_active
    global price_label_text, round_label_text, countdown_label_text, update_labels
    if (winner >= 0):
        price_label_text = f"{current_auction+1}. kolo aukce skončilo.\nVítězem kola se stal/a hráč/ka č. {winner+1}."
    else:
        price_label_text =f"{current_auction+1}. kolo aukce skončilo.\nKolo nemá vítěze."
    update_labels = True
    #update_window()
    current_auction += 1
    auction_active = False
    if current_auction < num_auctions:
        evaluate_winner(False)
        countdown_timer(5, f"Startovní cena se zobrazí")  # 5 sekundový odpočet před začátkem aukce
        run_auction()
    else:
        evaluate_winner(True)
        countdown_label_text = "Všechna kola aukce skončila."
        print("Všechna kola aukce skončila.")
        current_auction = 0  # Reset pro další kolo aukcí
    update_labels = True

def player_action(player_index):
    print(f"Hráč {player_index} stiskl.")
    global auction_active
    if auction_active and registered_players[player_index]:
        auction_active = False
        scores[player_index] += current_price
        win_rounds[player_index] += 1
        #update_table()
        handle_auction_end(player_index)  # Řízení konce aukce a možné spuštění nové aukce
        global scores_updated
        scores_updated = True

def start_auction():
    global registration_active, current_auction
    if sum(registered_players) < 2:
        print("Není dostatek přihlášených hráčů - čekáme na další.")
        return

    registration_active = False
    current_auction = 0
    run_auction()

def register_players():
    global registration_active
    global price_label_text, round_label_text, countdown_label_text, update_labels
    registration_active = True
    price_label_text="Probíhá registrace do hry.\nChcete-li hrát, stiskněte tlačítko."
    round_label_text=""
    countdown_label_text="Stiskněte tlačítko a registrujte se do hry."
    update_labels = True
    while sum(registered_players) < 2:
        update_window()
        sleep(0.1)
    price_label_text="Probíhá registrace do hry.\nPoslední možnost se přihlásit."
    start_button.config(state=tk.NORMAL)  # Enable start button after registration of 2 players
    countdown_timer(10, "Registrace hráčů končí")  # 20 sekundový odpočet před začátkem dalsi hry
    if registration_active:
        start_auction()
    countdown_timer(20, "Registrace hráčů proběhne")  # 20 sekundový odpočet před začátkem dalsi hry
    update_table()
    reset_game()


def reset_game():
    global scores, win_rounds, registered_players, auction_active, registration_active, current_auction
    scores = [0] * num_players
    win_rounds = [0] * num_players
    registered_players = [False] * num_players
    auction_active = False
    registration_active = True
    current_auction = 0
    #for label in player_labels:
    #    label.config(text=label['text'].split(':')[0] + ': 0')
    update_table()
    update_window()
    start_button.config(state=tk.DISABLED)
    register_players()

def button_pressed(button, index):
    """Funkce reaguje na stisk tlačítka přes GPIO."""
    player_index = buttons.index(button)  # Získání indexu tlačítka
    if registration_active:
        registered_players[player_index] = True
        print(f"Hráč č. {player_index + 1} registrován tlačítkem.")
        global registration_updated
        registration_updated = True
    elif auction_active:
        player_action(player_index)
    #print(f"Tlačítko {index + 1} bylo stisknuto hráčem {player_index + 1}.")

        

# Přiřazení funkce k tlačítku, předpokládáme že `buttons` je seznam Button objektů z gpiozero
for i, button in enumerate(buttons):
    button.when_pressed = lambda button=button, i=i: button_pressed(button, i)

def handle_key_press(event, player_index):
    if registration_active:
        registered_players[player_index] = True
        #update_table()
        print(f"Hráč č. {player_index + 1} registrován klávesnicí.")
        global registration_updated
        registration_updated = True
    elif auction_active:
        player_action(player_index)


def update_table():
    global scores, win_rounds, registered_players, num_players
    for i in range(num_players):
        if registered_players[i]:
            window.after(0, lambda i=i: tree.item(i, values=(f"Hráč {i + 1}", scores[i], win_rounds[i])))
        else:
            window.after(0, lambda i=i: tree.item(i, values=(f"Hráč {i + 1}", "nehraje", "")))
    pass

def periodic_check():
    global registration_updated, scores_updated, update_labels
    global price_label_text, round_label_text, countdown_label_text
    if registration_updated:
        update_table()
        registration_updated = False
    if scores_updated:
        update_table()
        scores_updated = False
    if update_labels:
        update_table()
        price_label.config(text=price_label_text)
        round_label.config(text=round_label_text)
        countdown_label.config(text=countdown_label_text)
        update_labels = False
    update_window()
    window.after(100, periodic_check)

#dekorátor pro exception při zavírání okna
def catch_tcl_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tk.TclError as e:
            #print("TclError caught:", e)
            sys.exit()
    return wrapper

@catch_tcl_error
def update_window():
    window.update()
    pass


# GUI setup
window = tk.Tk()
window.after(100, periodic_check)
window.title("Dutch Auction Game")
window.wm_attributes('-fullscreen', 'true')  # Otevře okno v režimu celé obrazovky

# Nastavení min. šířky sloupců
#window.columnconfigure(0, weight=1)
#window.columnconfigure(1, weight=1)
#window.columnconfigure(2, weight=1)

# Vytvoření tří widgetů Label, jeden pro každý sloupec
#label1 = tk.Label(window, text="Sloupec 1", bg="red")
#label1.grid(row=0, column=0, sticky="nsew")  # 'nsew' roztažení na všechny strany

#label2 = tk.Label(window, text="Sloupec 2", bg="green")
#label2.grid(row=0, column=1, sticky="nsew")

#label3 = tk.Label(window, text="Sloupec 3", bg="blue")
#label3.grid(row=0, column=2, sticky="nsew")


# Gauge plot setup
fig = Figure(figsize=(8, 4))
ax = fig.add_subplot(111, polar=True)
ax.barh(1, np.radians(180), left=np.radians(180), height=1, color='lightgray')
ax.set_ylim(0, 1)
ax.grid(False)
ax.set_xticks([])
ax.set_yticks([])

canvas = FigureCanvasTkAgg(fig, master=window)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()

def draw_gauge(value, max_value=1500):
    # Vymazání pouze obsahu grafu, ne celého grafu
    if hasattr(draw_gauge, 'needle'):
        draw_gauge.needle.remove()  # Odstranění staré ručičky
    norm_value = value / max_value
    angle = np.radians(180 - norm_value * 180)
    draw_gauge.needle = ax.plot([angle, angle], [0, 1], color='red', lw=2)[0]  # Uložení referenci na novou ručičku

    # Kontrola, zda textový objekt již existuje
    if hasattr(draw_gauge, 'value_text'):
        draw_gauge.value_text.set_text(str(value))  # Aktualizace existujícího textu
    else:
        # Vytvoření nového textového objektu, pokud ještě neexistuje
        draw_gauge.value_text = ax.text(np.pi * 1.5, 0.7, str(value), ha='center', va='center', fontsize=12, color='blue')

    canvas.draw_idle()  # Optimalizované překreslení


draw_gauge(1500)  # Startovní hodnota gauge

price_label = tk.Label(window, text=f"Celková cena: {total_sum}\n", font=('Helvetica', 18))
#price_label.grid(row=0, column=1)
price_label.pack(pady=20)

round_label = tk.Label(window, text="", font=('Helvetica', 16))
#round_label.grid(row=0, column=1)
round_label.pack(pady=20)

countdown_label = tk.Label(window, text="Stiskněte tlačítko a registrujte se do hry.", font=('Helvetica', 16))
#countdown_label.grid(row=0, column=1)
countdown_label.pack(pady=10)


style = ttk.Style()
style.theme_use('clam')  # Použijeme téma 'clam', které umožňuje úpravy // alt, default, classic, clam, aqua

# Definování stylů pro normální a vítězné řádky
style.map('Treeview', background=[('selected', 'blue')])
style.configure('Treeview', background='white', fieldbackground='white')
style.configure('Winner.Treeview', background='gold')
style.configure("Treeview", font=('Helvetica', 14))  # Nastavení velikosti písma
style.configure("Treeview.Heading", font=('Helvetica', 18))  # Zvětšení písma pro záhlaví
style.configure("Treeview.Rowheight", rowheight=10)  # Nastavení výšky řádku

# Vytvoření Treeview widgetu
tree = ttk.Treeview(window, columns=("Player", "Score", "Wins"), show="headings", height=5)
tree.heading("Player", text="Hráč")
tree.heading("Score", text="Součet ceny")
tree.heading("Wins", text="Počet výher")
tree.column("Score", anchor=tk.E) #zarovnání doprava
tree.column("Wins", anchor=tk.E) #zarovnání doprava
# Nastavení tagu a stylu pro vítěze
tree.tag_configure('normal', background='white')  # Normální pozadí
tree.tag_configure('winner', background='gold')   # Zvýrazněné pozadí pro vítěze

def adjust_row_height(tree, height=30):
    """Nastaví výšku řádku Treeview vytvořením transparentního obrázku s požadovanou výškou."""
    # Vytvoření transparentního obrázku o požadované výšce
    img = tk.PhotoImage(height=height, width=1)
    tree.img = img  # Uložení obrázku, aby nebyl odstraněn garbage collectorem
    for item in tree.get_children():
        tree.item(item, image=img)  # Přiřazení obrázku k položkám
# Nastavení výšky řádku
adjust_row_height(tree)

#tree.grid(row=0, column=1)
tree.pack(pady=20)

# Inicializace tabulky s hráči
for i in range(num_players):
    tree.insert("", "end", iid=i, values=(f"Hráč {i + 1}", scores[i], win_rounds[i]))

start_button = tk.Button(window, text="Zahájit hru", command=start_auction, state=tk.DISABLED)
#start_button.grid(row=0, column=1)
start_button.pack(pady=20)

reset_button = tk.Button(window, text="Resetovat hru", command=reset_game)
#reset_button.grid(row=0, column=1)
reset_button.pack(pady=10)

# Klávesnicové zkratky pro hráče a startovací tlačítko
key_map = {'a': 0, 'd': 1, 'g': 2, 'j': 3, 'l': 4}
for key, player_index in key_map.items():
    window.bind(key, lambda event, index=player_index: handle_key_press(event, index))
window.bind('u', lambda event: start_auction() if not auction_active else None)

window.bind('<r>', lambda e: reset_game())  # Bind 'r' key for reset
window.bind('<q>', lambda e: window.quit())  # Bind 'q' key to quit

#app = GaugeAnimation(window)

update_table()


# Testování
test_leds()

register_players()  # Start registration process

window.mainloop()

