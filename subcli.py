#!/usr/bin/env python3
# Консольный редактор текста с функционалом Sublime Text для InteriumOS

import os
import sys
import curses
import codecs

# Путь к файлам пользователя
USER_HOME = os.path.expanduser("~")

class EditorBuffer:
    def __init__(self, filename=None):
        self.filename = filename
        self.lines = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll = 0
        self.modified = False
        if filename and os.path.exists(filename):
            with codecs.open(filename, "r", encoding="utf-8", errors="replace") as f:
                self.lines = [line.rstrip("\n\r") for line in f]
            if not self.lines:
                self.lines = [""]
        self.search_term = ""
        self.search_results = []
        self.search_index = 0

    def insert(self, ch):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x += len(ch)
        self.modified = True

    def backspace(self):
        if self.cursor_x == 0 and self.cursor_y > 0:
            prev_len = len(self.lines[self.cursor_y - 1])
            self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
            del self.lines[self.cursor_y]
            self.cursor_y -= 1
            self.cursor_x = prev_len
            self.modified = True
        elif self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified = True

    def delete(self):
        line = self.lines[self.cursor_y]
        if self.cursor_x < len(line):
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x+1:]
            self.modified = True
        elif self.cursor_y < len(self.lines) - 1:
            self.lines[self.cursor_y] += self.lines[self.cursor_y + 1]
            del self.lines[self.cursor_y + 1]
            self.modified = True

    def newline(self):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True

    def save(self, filename=None):
        if filename:
            self.filename = filename
        if self.filename:
            with codecs.open(self.filename, "w", encoding="utf-8") as f:
                for line in self.lines:
                    f.write(line + "\n")
            self.modified = False

    def goto(self, line):
        l = max(0, min(line-1, len(self.lines)-1))
        self.cursor_y = l
        self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))

    def search(self, term, direction=1):
        self.search_term = term
        self.search_results = []
        for idx, line in enumerate(self.lines):
            col = line.lower().find(term.lower())
            if col != -1:
                self.search_results.append((idx, col))
        if self.search_results:
            self.search_index = 0 if direction == 1 else len(self.search_results)-1
            self.goto_search_result()
        return bool(self.search_results)

    def goto_search_result(self):
        if self.search_results:
            y, x = self.search_results[self.search_index]
            self.cursor_y = y
            self.cursor_x = x

    def next_search(self):
        if self.search_results:
            self.search_index = (self.search_index + 1) % len(self.search_results)
            self.goto_search_result()

    def prev_search(self):
        if self.search_results:
            self.search_index = (self.search_index - 1) % len(self.search_results)
            self.goto_search_result()

    def replace(self, replacement):
        if self.search_results:
            y, x = self.search_results[self.search_index]
            line = self.lines[y]
            term = self.search_term
            self.lines[y] = line[:x] + replacement + line[x+len(term):]
            self.modified = True
            self.search(term)  # re-index

    def replace_all(self, replacement):
        count = 0
        for idx, line in enumerate(self.lines):
            if self.search_term.lower() in line.lower():
                self.lines[idx] = line.replace(self.search_term, replacement)
                count += 1
        self.modified = True
        return count

class SublimeCLI:
    def __init__(self, stdscr, filename=None):
        self.stdscr = stdscr
        self.buffers = []
        self.current = 0
        self.status_msg = ""
        self.quit = False
        curses.curs_set(1)
        self.open_buffer(filename)
        # Исправленная таблица управления Ctrl+буква
        self.keymap = {
            19: self.save,        # Ctrl+S
            15: self.open_file,   # Ctrl+O
            17: self.close,       # Ctrl+Q
            14: self.new,         # Ctrl+N
            23: self.close_buffer,# Ctrl+W
            6: self.find,         # Ctrl+F
            18: self.replace,     # Ctrl+R
            7: self.goto,         # Ctrl+G
            16: self.command_palette, # Ctrl+P
            20: self.next_buffer, # Ctrl+T
        }

    def open_buffer(self, filename=None):
        buf = EditorBuffer(filename)
        self.buffers.append(buf)
        self.current = len(self.buffers) - 1

    def run(self):
        while not self.quit:
            self.render()
            key = self.stdscr.getch()
            self.process_key(key)

    def render(self):
        self.stdscr.clear()
        maxy, maxx = self.stdscr.getmaxyx()
        buf = self.buffers[self.current]
        # Draw tabs
        tabline = ""
        for idx, b in enumerate(self.buffers):
            t = os.path.basename(b.filename) if b.filename else "untitled"
            if b.modified:
                t += "*"
            if idx == self.current:
                tabline += f"[{t}] "
            else:
                tabline += f" {t}  "
        self.stdscr.addstr(0, 0, tabline[:maxx-1], curses.A_REVERSE)
        # Draw buffer
        h = maxy - 2
        w = maxx - 1
        for i in range(h):
            li = buf.scroll + i
            if li < len(buf.lines):
                line = buf.lines[li].replace("\t", "    ")
                self.stdscr.addstr(i+1, 0, line[:w])
        # Draw status bar
        fname = buf.filename or "untitled"
        status = f"{fname} | Ln {buf.cursor_y+1}, Col {buf.cursor_x+1} {'*' if buf.modified else ''} | Ctrl+P:Cmd | Ctrl+Q:Quit"
        self.stdscr.addstr(maxy-1, 0, status[:maxx-1], curses.A_REVERSE)
        if self.status_msg:
            self.stdscr.addstr(maxy-2, 0, self.status_msg[:maxx-1], curses.A_BOLD)
        # Set cursor
        pos_y = buf.cursor_y - buf.scroll + 1
        pos_x = buf.cursor_x
        if 1 <= pos_y < maxy-1:
            self.stdscr.move(pos_y, min(pos_x, maxx-2))

    def process_key(self, key):
        buf = self.buffers[self.current]
        # Keymap
        if key in self.keymap:
            self.keymap[key]()
            return
        # Navigation
        elif key == curses.KEY_UP:
            if buf.cursor_y > 0:
                buf.cursor_y -= 1
                buf.cursor_x = min(buf.cursor_x, len(buf.lines[buf.cursor_y]))
                if buf.cursor_y < buf.scroll:
                    buf.scroll = buf.cursor_y
        elif key == curses.KEY_DOWN:
            if buf.cursor_y < len(buf.lines) - 1:
                buf.cursor_y += 1
                buf.cursor_x = min(buf.cursor_x, len(buf.lines[buf.cursor_y]))
                maxy, _ = self.stdscr.getmaxyx()
                if buf.cursor_y >= buf.scroll + maxy - 2:
                    buf.scroll += 1
        elif key == curses.KEY_LEFT:
            if buf.cursor_x > 0:
                buf.cursor_x -= 1
            elif buf.cursor_y > 0:
                buf.cursor_y -= 1
                buf.cursor_x = len(buf.lines[buf.cursor_y])
        elif key == curses.KEY_RIGHT:
            if buf.cursor_x < len(buf.lines[buf.cursor_y]):
                buf.cursor_x += 1
            elif buf.cursor_y < len(buf.lines) - 1:
                buf.cursor_y += 1
                buf.cursor_x = 0
        elif key in (curses.KEY_ENTER, 10, 13):
            buf.newline()
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            buf.backspace()
        elif key == curses.KEY_DC:
            buf.delete()
        elif key == 9:  # Tab
            buf.insert("    ")
        elif 32 <= key <= 126:
            buf.insert(chr(key))
        # Scroll
        elif key == curses.KEY_PPAGE:
            buf.scroll = max(0, buf.scroll - 10)
        elif key == curses.KEY_NPAGE:
            buf.scroll = min(max(0, len(buf.lines) - 1), buf.scroll + 10)
        # Fallback: ignore
        else:
            pass

    def save(self):
        buf = self.buffers[self.current]
        if not buf.filename:
            self.status_msg = "Save as: "
            curses.echo()
            self.stdscr.move(curses.LINES-2, len(self.status_msg))
            fname = self.stdscr.getstr().decode()
            curses.noecho()
            if fname:
                buf.save(fname)
                self.status_msg = f"Saved: {fname}"
            else:
                self.status_msg = "Save cancelled"
        else:
            buf.save()
            self.status_msg = f"Saved: {buf.filename}"

    def open_file(self):
        self.status_msg = "Open file: "
        curses.echo()
        self.stdscr.move(curses.LINES-2, len(self.status_msg))
        fname = self.stdscr.getstr().decode()
        curses.noecho()
        if fname:
            self.open_buffer(fname)
            self.status_msg = f"Opened: {fname}"
        else:
            self.status_msg = "Open cancelled"

    def close(self):
        self.quit = True

    def new(self):
        self.open_buffer(None)
        self.status_msg = "New file"

    def close_buffer(self):
        if len(self.buffers) > 1:
            self.buffers.pop(self.current)
            self.current = max(0, self.current - 1)
            self.status_msg = "Closed buffer"
        else:
            self.status_msg = "Can't close last buffer"

    def next_buffer(self):
        if len(self.buffers) > 1:
            self.current = (self.current + 1) % len(self.buffers)
            self.status_msg = f"Switched to buffer {self.current+1}"

    def find(self):
        self.status_msg = "Find: "
        curses.echo()
        self.stdscr.move(curses.LINES-2, len(self.status_msg))
        term = self.stdscr.getstr().decode()
        curses.noecho()
        if term:
            found = self.buffers[self.current].search(term)
            if found:
                self.status_msg = f"Found: {term}"
            else:
                self.status_msg = f"Not found: {term}"

    def replace(self):
        self.status_msg = "Replace: "
        curses.echo()
        self.stdscr.move(curses.LINES-2, len(self.status_msg))
        repl = self.stdscr.getstr().decode()
        curses.noecho()
        if repl:
            count = self.buffers[self.current].replace_all(repl)
            self.status_msg = f"Replaced {count} occurences"
        else:
            self.status_msg = "Replace cancelled"

    def goto(self):
        self.status_msg = "Goto line: "
        curses.echo()
        self.stdscr.move(curses.LINES-2, len(self.status_msg))
        s = self.stdscr.getstr().decode()
        curses.noecho()
        try:
            l = int(s)
            self.buffers[self.current].goto(l)
            self.status_msg = f"Went to line {l}"
        except Exception:
            self.status_msg = "Goto cancelled"

    def command_palette(self):
        self.status_msg = "Command (save, open, new, close, next, find, replace, goto, quit): "
        curses.echo()
        self.stdscr.move(curses.LINES-2, len(self.status_msg))
        cmd = self.stdscr.getstr().decode().strip().lower()
        curses.noecho()
        if cmd == "save":
            self.save()
        elif cmd == "open":
            self.open_file()
        elif cmd == "new":
            self.new()
        elif cmd == "close":
            self.close_buffer()
        elif cmd == "next":
            self.next_buffer()
        elif cmd == "find":
            self.find()
        elif cmd == "replace":
            self.replace()
        elif cmd == "goto":
            self.goto()
        elif cmd == "quit":
            self.close()
        else:
            self.status_msg = f"Unknown command: {cmd}"

def main(stdscr):
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None
    editor = SublimeCLI(stdscr, filename)
    editor.run()

if __name__ == "__main__":
    curses.wrapper(main)