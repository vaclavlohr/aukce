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
    for i in range(count, 0, -1):
        countdown_label.config(text=f"{action} za {i} sekund.")
        update_window()
        sleep(1)
    #countdown_label.config(text=f"{action} právě probíhá.")
    countdown_label.config(text="")
    update_window()

def run_auction():
    global current_price, auction_active, current_auction, final_values, auction_countdown
    #current_price = 1000
    current_price = final_values[current_auction]
    bid_decrement = np.random.randint(2, 11)
    registration_active = False

    #countdown_timer(5, "auction round")  # 5 sekundový odpočet před začátkem aukce

    price_label.config(text=f"Startovní cena: {current_price}\n")
    round_label.config(text=f"Kolo aukce #{current_auction+1} z {num_auctions}")
    draw_gauge(current_price)
    update_window()

    if (not auction_countdown): 
        auction_countdown = True

        countdown_timer(5, f"{current_auction+1}. kolo aukce začne")  # 5 sekundový odpočet před začátkem aukce

        auction_countdown = False
        auction_active = True

        while auction_active and current_price > 0:
            current_price -= bid_decrement
            price_label.config(text=f"Cena: {current_price}\n")
            draw_gauge(current_price)
            update_window()
            #sleep(0.01)  # Zkrácený čas pro dynamickou aukci

        if auction_active:
            handle_auction_end(-1) #No winner

def evaluate_winner(final):
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
        round_label.config(text=f"Průběžným vítězem aukce je: Hráč {winner_index + 1} s {win_rounds[winner_index]} výhrami a skóre {scores[winner_index]}")
    if (final == True):
        round_label.config(text=f"Celkovým vítězem aukce je: Hráč {winner_index + 1} s {win_rounds[winner_index]} výhrami a skóre {scores[winner_index]}")
    
    # Zvýraznění vítěze v Treeview
    for child in tree.get_children():
        tree.item(child, tags=('normal',))  # Resetování všech značek
    tree.item(tree.get_children()[winner_index], tags=('winner',))
    
    update_window()

def handle_auction_end(winner):
    global current_auction, auction_active
    if (winner >= 0):
        price_label.config(text=f"{current_auction+1}. kolo aukce skončilo.\nVítězem kola se stal/a hráč/ka č. {winner+1}.")
    else:
        price_label.config(text=f"{current_auction+1}. kolo aukce skončilo.\nKolo nemá vítěze.")        
    update_window()
    current_auction += 1
    auction_active = False
    if current_auction < num_auctions:
        evaluate_winner(False)
        countdown_timer(5, f"Startovní cena se zobrazí")  # 5 sekundový odpočet před začátkem aukce
        run_auction()
    else:
        evaluate_winner(True)
        countdown_label.config(text="Všechna kola aukce skončila.")
        print("Všechna kola aukce skončila.")
        current_auction = 0  # Reset pro další kolo aukcí

def player_action(player_index):
    global auction_active
    if auction_active and registered_players[player_index]:
        auction_active = False
        scores[player_index] += current_price
        win_rounds[player_index] += 1
        update_table()
        handle_auction_end(player_index)  # Řízení konce aukce a možné spuštění nové aukce

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
    registration_active = True
    price_label.config(text="Probíhá registrace do hry.\nChcete-li hrát, stiskněte tlačítko.")
    round_label.config(text="")
    countdown_label.config(text="Stiskněte tlačítko a registrujte se do hry.")
    while sum(registered_players) < 2:
        update_window()
        sleep(0.1)
    price_label.config(text="Probíhá registrace do hry.\nPoslední možnost se přihlásit.")
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

def button_pressed(button):
    player_index = buttons.index(button)
    if registration_active:
        registered_players[player_index] = True
        #player_labels[player_index].config(text=f"Player {player_index + 1} (Registered): {scores[player_index]}")
        #player_labels[player_index].config(text=f"Hráč č. {player_index + 1} registrován.")
        print(f"Hráč č. {player_index + 1} registrován.")
    elif auction_active:
        player_action(player_index)

for button in buttons:
    button.when_pressed = button_pressed

def handle_key_press(event, player_index):
    if registration_active:
        registered_players[player_index] = True
        update_table()
        #player_labels[player_index].config(text=f"Hráč č. {player_index + 1} registrován: {scores[player_index]}")
        print(f"Hráč č. {player_index + 1} registrován.")
    elif auction_active:
        player_action(player_index)
        

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


# GUI setup
window = tk.Tk()
window.title("Dutch Auction Game")


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
price_label.pack(pady=20)

round_label = tk.Label(window, text="", font=('Helvetica', 16))
round_label.pack(pady=20)

countdown_label = tk.Label(window, text="Stiskněte tlačítko a registrujte se do hry.", font=('Helvetica', 16))
countdown_label.pack(pady=10)


style = ttk.Style()
style.theme_use('clam')  # Použijeme téma 'clam', které umožňuje úpravy

# Definování stylů pro normální a vítězné řádky
style.map('Treeview', background=[('selected', 'blue')])
style.configure('Treeview', background='white', fieldbackground='white')
style.configure('Winner.Treeview', background='gold')

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
tree.pack(pady=20)

# Inicializace tabulky s hráči
for i in range(num_players):
    tree.insert("", "end", iid=i, values=(f"Hráč {i + 1}", scores[i], win_rounds[i]))

def update_table():
    for i in range(num_players):
        if (registered_players[i]):
            tree.item(i, values=(f"Hráč {i + 1}", scores[i], win_rounds[i]))
        else:
            tree.item(i, values=(f"Hráč {i + 1}", "nehraje", ""))

start_button = tk.Button(window, text="Zahájit hru", command=start_auction, state=tk.DISABLED)
start_button.pack(pady=20)

reset_button = tk.Button(window, text="Resetovat hru", command=reset_game)
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
register_players()  # Start registration process

window.mainloop()

