#!/usr/bin/env python3
import curses
import subprocess
import json

def draw_header(stdscr):
    """Rysuje nagłówek z powitaniem w kolorze cyan oraz krótką instrukcję."""
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(0, 0, "Witaj w Pawel Music!")
    stdscr.attroff(curses.color_pair(1))
    stdscr.addstr(2, 0, "Użyj strzałek aby wybrać opcję i Enter aby zatwierdzić.")

def curses_menu(stdscr, options, start_y):
    """Wyświetla menu sterowane strzałkami i zwraca indeks wybranej opcji."""
    current_selection = 0
    while True:
        # Czyścimy obszar menu
        for i in range(start_y, start_y + len(options) + 2):
            stdscr.move(i, 0)
            stdscr.clrtoeol()
        draw_header(stdscr)
        for idx, option in enumerate(options):
            if idx == current_selection:
                stdscr.addstr(start_y + idx, 0, option, curses.A_REVERSE)
            else:
                stdscr.addstr(start_y + idx, 0, option)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(options)
        elif key in [10, 13]:  # Enter
            return current_selection

def search_option(stdscr):
    """
    Obsługuje tryb wyszukiwania:
      - Pyta o nazwę utworu.
      - Używa yt-dlp w trybie JSON (z --flat-playlist) do pobrania 5 wyników.
      - Wyświetla wyniki i prosi o wpisanie ID utworu.
    """
    stdscr.clear()
    draw_header(stdscr)
    stdscr.addstr(4, 0, "Podaj nazwę utworu: ")
    stdscr.refresh()
    curses.echo()
    query = stdscr.getstr(4, len("Podaj nazwę utworu: ") + 1, 60).decode("utf-8").strip()
    curses.noecho()
    
    try:
        # Używamy --flat-playlist i -J, żeby zwrócić cały wynik jako JSON
        cmd = ["yt-dlp", "--flat-playlist", "-J", f"ytsearch5:{query}"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=30).decode("utf-8")
        data = json.loads(output)
    except subprocess.TimeoutExpired:
        stdscr.addstr(6, 0, "Wyszukiwanie trwało zbyt długo!")
        stdscr.refresh()
        stdscr.getch()
        return None
    except Exception as e:
        stdscr.addstr(6, 0, "Błąd podczas wyszukiwania:")
        stdscr.addstr(7, 0, str(e))
        stdscr.refresh()
        stdscr.getch()
        return None

    # Odczytujemy wyniki – spodziewamy się, że data ma klucz "entries"
    entries = data.get("entries", [])
    results = []
    for entry in entries:
        video_id = entry.get("id")
        title = entry.get("title", "Brak tytułu")
        if video_id:
            results.append((video_id, title))
    
    if not results:
        stdscr.addstr(6, 0, "Nie znaleziono wyników wyszukiwania.")
        stdscr.refresh()
        stdscr.getch()
        return None

    stdscr.clear()
    draw_header(stdscr)
    stdscr.addstr(4, 0, "Wyniki wyszukiwania:")
    for idx, (vid_id, title) in enumerate(results):
        stdscr.addstr(6 + idx, 0, f"{idx+1}. {title} (ID: {vid_id})")
    stdscr.addstr(6 + len(results) + 1, 0, "Wpisz ID utworu: ")
    stdscr.refresh()
    curses.echo()
    chosen_id = stdscr.getstr(6 + len(results) + 1, len("Wpisz ID utworu: ") + 1, 20).decode("utf-8").strip()
    curses.noecho()
    return chosen_id

def saved_option(stdscr):
    """
    Obsługuje tryb 'Proponowane' – prezentuje stałą listę utworów i zwraca wybrane ID.
    Lista zawiera:
      - Po twojej pysznej zupie    (ID: 3VizXab7XE0)
      - Kibel                      (ID: n1qxMA7miyk)
      - Babka najlepsza jest przez duże B (ID: JG1_B_nVBCg)
      - Hehe papież tańczy         (ID: 2yusdx60_aw)
      - Dyche daj robotowi         (ID: JPveQux2WWo)
      - Macarena                   (ID: WaymcVmJ-A)
    """
    saved_songs = [
        ("Po twojej pysznej zupie", "3VizXab7XE0"),
        ("Kibel", "n1qxMA7miyk"),
        ("Babka najlepsza jest przez duże B", "JG1_B_nVBCg"),
        ("Hehe papież tańczy", "2yusdx60_aw"),
        ("Dyche daj robotowi", "JPveQux2WWo"),
        ("Macarena", "zWaymcVmJ-A")
    ]
    options = [song[0] for song in saved_songs]
    stdscr.clear()
    draw_header(stdscr)
    stdscr.addstr(4, 0, "Wybierz utwór z Proponowanych:")
    selected_index = curses_menu(stdscr, options, start_y=6)
    return saved_songs[selected_index][1]

def main(stdscr):
    # Inicjalizacja kolorów (cyan dla nagłówka)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    
    stdscr.clear()
    draw_header(stdscr)
    stdscr.refresh()
    
    menu_options = ["Szukaj", "Proponowane"]
    selected = curses_menu(stdscr, menu_options, start_y=4)
    
    if selected == 0:
        chosen_id = search_option(stdscr)
    else:
        chosen_id = saved_option(stdscr)
    return chosen_id

if __name__ == "__main__":
    video_id = curses.wrapper(main)
    if video_id:
        # Dodajemy opcję --no-video, żeby odtwarzać tylko audio
        subprocess.run(["mpv", "--no-video", f"https://www.youtube.com/watch?v={video_id}"])
