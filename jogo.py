import asyncio
import json
import math
import os
import random
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

import pygame

# ============================================================
# LOJA DO ZERO
# Protótipo 2D de gerenciamento de loja em Python/Pygame.
# Compatível com desktop e preparado para pygbag/WebAssembly.
# ============================================================

WIDTH, HEIGHT = 1280, 720
FPS = 60
SAVE_FILE = "loja_do_zero_save.json"
VERSION = 1

# ---------- Tema visual original ----------
BG = (238, 242, 247)
PANEL = (255, 255, 255)
INK = (34, 39, 52)
MUTED = (111, 120, 137)
PRIMARY = (92, 86, 230)
PRIMARY_DARK = (70, 64, 180)
SUCCESS = (50, 174, 112)
WARNING = (236, 166, 61)
DANGER = (223, 80, 91)
CYAN = (54, 176, 202)
PURPLE = (141, 91, 205)
WOOD = (185, 136, 84)
WOOD_DARK = (126, 85, 45)
FLOOR = (248, 249, 252)
WALL = (224, 228, 236)
BLACK = (15, 17, 24)
WHITE = (255, 255, 255)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def draw_round_rect(surface, rect, color, radius=12, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def text(surface, font, content, pos, color=INK, anchor="topleft"):
    image = font.render(str(content), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect


@dataclass
class Product:
    key: str
    name: str
    icon: str
    buy_price: float
    sell_price: float
    unlock_level: int
    color: Tuple[int, int, int]

    @property
    def profit(self):
        return self.sell_price - self.buy_price


PRODUCTS: Dict[str, Product] = {
    "apple": Product("apple", "Maçã", "MAC", 2.0, 4.0, 1, (230, 86, 96)),
    "bread": Product("bread", "Pão", "PAO", 2.5, 5.0, 1, (218, 157, 70)),
    "milk": Product("milk", "Leite", "LEI", 3.0, 6.0, 1, (130, 170, 220)),
    "chocolate": Product("chocolate", "Chocolate", "CHO", 5.0, 10.0, 2, (121, 78, 74)),
    "soda": Product("soda", "Refrigerante", "REF", 4.5, 9.0, 2, (85, 154, 222)),
    "pizza": Product("pizza", "Pizza", "PIZ", 10.0, 20.0, 3, (239, 124, 70)),
    "headphones": Product("headphones", "Fone", "FON", 18.0, 38.0, 3, (129, 108, 205)),
    "console": Product("console", "Videogame", "VID", 55.0, 105.0, 4, (91, 95, 105)),
    "phone": Product("phone", "Celular", "CEL", 90.0, 170.0, 4, (81, 157, 152)),
    "computer": Product("computer", "Computador", "PC", 180.0, 330.0, 5, (92, 104, 132)),
}

LEVELS = {
    1: ("Mercadinho", 0, 3, 2),
    2: ("Loja de Bairro", 250, 6, 4),
    3: ("Supermercado", 900, 10, 6),
    4: ("Mega Loja", 2200, 16, 9),
    5: ("Loja Premium", 5000, 22, 12),
}

UPGRADES = {
    "shelves": {"name": "Mais prateleiras", "base": 80, "step": 55, "desc": "+1 espaço de produto na loja"},
    "space": {"name": "Mais espaço", "base": 150, "step": 100, "desc": "+2 clientes simultâneos"},
    "lighting": {"name": "Iluminação", "base": 120, "step": 90, "desc": "+4 satisfação"},
    "warehouse": {"name": "Estoque maior", "base": 100, "step": 70, "desc": "+15 capacidade por produto"},
    "cleaning": {"name": "Limpeza", "base": 90, "step": 60, "desc": "+5 satisfação base"},
    "entrance": {"name": "Entrada maior", "base": 180, "step": 120, "desc": "+1 cliente simultâneo"},
}

EMPLOYEES = {
    "cashier": {"name": "Caixa", "cost": 280, "salary": 4.0, "benefit": "Atende clientes mais rápido"},
    "stock": {"name": "Repositor", "cost": 360, "salary": 5.0, "benefit": "Repõe 1 unidade por segundo"},
    "cleaner": {"name": "Faxineiro", "cost": 420, "salary": 5.5, "benefit": "+8 satisfação e limpeza automática"},
}

EVENTS = [
    {"key": "sale", "title": "Promoção do dia", "message": "Produtos selecionados vendem 50% mais rápido!", "duration": 25},
    {"key": "rush", "title": "Movimento intenso", "message": "Mais clientes estão chegando por alguns segundos.", "duration": 22},
    {"key": "supplier", "title": "Oferta do fornecedor", "message": "Reposição de estoque 35% mais barata.", "duration": 25},
]

MISSIONS = [
    {"key": "first_sale", "title": "Primeira venda", "desc": "Faça sua primeira venda.", "reward": 50, "target": 1},
    {"key": "first_profit", "title": "Primeiro lucro", "desc": "Ganhe R$ 100 em vendas.", "reward": 100, "target": 100},
    {"key": "level_2", "title": "Loja crescendo", "desc": "Chegue ao nível 2.", "reward": 100, "target": 2},
    {"key": "customers_50", "title": "Clientela fiel", "desc": "Atenda 50 clientes.", "reward": 150, "target": 50},
    {"key": "sales_100", "title": "Máquina de vendas", "desc": "Faça 100 vendas.", "reward": 300, "target": 100},
]

ACHIEVEMENTS = [
    ("first_customer", "Primeiro Cliente", "Atenda seu primeiro cliente."),
    ("sales_100", "100 Vendas", "Realize 100 vendas."),
    ("revenue_1000", "R$ 1.000 em vendas", "Alcance R$ 1.000 em faturamento."),
    ("level_3", "Supermercado", "Chegue ao nível 3."),
    ("products_10", "10 Produtos", "Desbloqueie todos os produtos."),
    ("first_employee", "Primeiro Funcionário", "Contrate o primeiro funcionário."),
    ("mega_store", "Mega Loja", "Chegue ao nível 4."),
]


@dataclass
class Customer:
    kind: str
    x: float
    y: float
    state: str = "enter"
    target_product: Optional[str] = None
    order_amount: int = 1
    wait: float = 0.0
    speed: float = 70.0
    color: Tuple[int, int, int] = (95, 102, 120)
    purchased: bool = False
    lifetime: float = 0.0


@dataclass
class Popup:
    message: str
    x: float
    y: float
    life: float = 1.2
    color: Tuple[int, int, int] = SUCCESS


class SaveManager:
    """Save local em arquivo no desktop e localStorage quando executado via pygbag."""

    def __init__(self, filename=SAVE_FILE):
        self.filename = filename
        self.web = False
        try:
            import js  # type: ignore
            self.js = js
            self.web = hasattr(js, "window") and hasattr(js.window, "localStorage")
        except Exception:
            self.js = None

    def load(self):
        try:
            if self.web:
                raw = self.js.window.localStorage.getItem(self.filename)
                if raw:
                    return json.loads(str(raw))
            elif os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as handle:
                    return json.load(handle)
        except Exception:
            return None
        return None

    def save(self, data):
        try:
            raw = json.dumps(data, ensure_ascii=False)
            if self.web:
                self.js.window.localStorage.setItem(self.filename, raw)
            else:
                temp = self.filename + ".tmp"
                with open(temp, "w", encoding="utf-8") as handle:
                    handle.write(raw)
                os.replace(temp, self.filename)
            return True
        except Exception:
            return False


class GameState:
    def __init__(self):
        self.money = 100.0
        self.level = 1
        self.total_sales = 0
        self.revenue = 0.0
        self.customers_served = 0
        self.xp = 0.0
        self.product_stock = {key: 0 for key in PRODUCTS}
        self.shelf_stock = {key: 0 for key in PRODUCTS}
        self.unlocked = [key for key, product in PRODUCTS.items() if product.unlock_level == 1]
        self.upgrades = {key: 0 for key in UPGRADES}
        self.employees = {key: 0 for key in EMPLOYEES}
        self.completed_missions: List[str] = []
        self.claimed_achievements: List[str] = []
        self.last_event_at = 0.0
        self.event: Optional[dict] = None
        self.event_ends_at = 0.0
        self.tutorial_step = 0
        self.tutorial_done = False
        self.restock_cooldown = 0.0
        self.day = 1
        self.day_seconds = 0.0
        self.daily_expenses = 0.0
        self.version = VERSION

    def to_dict(self):
        return {
            "version": self.version,
            "money": self.money,
            "level": self.level,
            "total_sales": self.total_sales,
            "revenue": self.revenue,
            "customers_served": self.customers_served,
            "xp": self.xp,
            "product_stock": self.product_stock,
            "shelf_stock": self.shelf_stock,
            "unlocked": self.unlocked,
            "upgrades": self.upgrades,
            "employees": self.employees,
            "completed_missions": self.completed_missions,
            "claimed_achievements": self.claimed_achievements,
            "tutorial_step": self.tutorial_step,
            "tutorial_done": self.tutorial_done,
            "day": self.day,
            "day_seconds": self.day_seconds,
        }

    def load_dict(self, data):
        for attr in ["money", "level", "total_sales", "revenue", "customers_served", "xp", "tutorial_step", "tutorial_done", "day", "day_seconds"]:
            if attr in data:
                setattr(self, attr, data[attr])
        for key in ["product_stock", "shelf_stock", "upgrades", "employees"]:
            src = data.get(key, {})
            target = getattr(self, key)
            for k in target:
                target[k] = src.get(k, target[k])
        self.unlocked = [k for k in data.get("unlocked", self.unlocked) if k in PRODUCTS]
        self.completed_missions = list(data.get("completed_missions", []))
        self.claimed_achievements = list(data.get("claimed_achievements", []))
        self.reconcile_unlocks()

    def reconcile_unlocks(self):
        for key, product in PRODUCTS.items():
            if product.unlock_level <= self.level and key not in self.unlocked:
                self.unlocked.append(key)

    def max_shelf_slots(self):
        return LEVELS[self.level][2] + self.upgrades["shelves"]

    def max_customers(self):
        return LEVELS[self.level][3] + self.upgrades["space"] * 2 + self.upgrades["entrance"]

    def warehouse_capacity(self, product_key):
        return 25 + self.upgrades["warehouse"] * 15

    def satisfaction(self):
        base = 68 + self.upgrades["lighting"] * 4 + self.upgrades["cleaning"] * 5
        if self.employees["cleaner"] > 0:
            base += 8 * self.employees["cleaner"]
        if not self.unlocked:
            base -= 15
        available = sum(self.shelf_stock.get(k, 0) > 0 for k in self.unlocked)
        variety_ratio = available / max(1, min(5, len(self.unlocked)))
        value = base + variety_ratio * 10
        return int(clamp(value, 15, 100))

    def next_level_target(self):
        if self.level >= 5:
            return LEVELS[5][1]
        return LEVELS[self.level + 1][1]

    def recalc_level(self):
        old_level = self.level
        for level in range(5, 0, -1):
            if self.revenue >= LEVELS[level][1]:
                self.level = level
                break
        self.reconcile_unlocks()
        return self.level != old_level


class ShopGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Loja do Zero")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fonts = self._build_fonts()
        self.state = GameState()
        self.save_manager = SaveManager()
        saved = self.save_manager.load()
        if saved:
            self.state.load_dict(saved)
        self.tab = "store"
        self.running = True
        self.customers: List[Customer] = []
        self.popups: List[Popup] = []
        self.notifications: List[Tuple[str, Tuple[int, int, int], float]] = []
        self.spawn_timer = 1.5
        self.autosave_timer = 0.0
        self.expense_timer = 0.0
        self.event_timer = random.uniform(30, 45)
        self.tutorial_overlay = True if not self.state.tutorial_done else False
        self.mouse_pos = (0, 0)
        self.clicks = []
        self.last_time = time.time()

    def _build_fonts(self):
        return {
            "tiny": pygame.font.SysFont("arial", 14),
            "small": pygame.font.SysFont("arial", 17),
            "body": pygame.font.SysFont("arial", 20),
            "medium": pygame.font.SysFont("arial", 24, bold=True),
            "large": pygame.font.SysFont("arial", 32, bold=True),
            "title": pygame.font.SysFont("arial", 42, bold=True),
        }

    def notify(self, message, color=SUCCESS):
        self.notifications.append((message, color, 3.0))

    def popup(self, message, x, y, color=SUCCESS):
        self.popups.append(Popup(message, x, y, 1.25, color))

    def resize_scale(self):
        width, height = self.screen.get_size()
        scale = min(width / WIDTH, height / HEIGHT)
        scaled_w, scaled_h = int(WIDTH * scale), int(HEIGHT * scale)
        offset_x = (width - scaled_w) // 2
        offset_y = (height - scaled_h) // 2
        return scale, offset_x, offset_y

    def logical_mouse(self):
        scale, ox, oy = self.resize_scale()
        mx, my = pygame.mouse.get_pos()
        if scale <= 0:
            return 0, 0
        return int((mx - ox) / scale), int((my - oy) / scale)

    def update(self, dt):
        self.mouse_pos = self.logical_mouse()
        self.autosave_timer += dt
        self.expense_timer += dt
        self.state.day_seconds += dt

        if self.autosave_timer > 8:
            self.autosave_timer = 0
            self.save()

        if self.state.day_seconds >= 120:
            self.state.day += 1
            self.state.day_seconds -= 120
            self.notify(f"Dia {self.state.day}: novas oportunidades na loja!", CYAN)

        # Salários simples por intervalo de 30 segundos.
        if self.expense_timer >= 30:
            self.expense_timer -= 30
            salaries = sum(v * EMPLOYEES[k]["salary"] for k, v in self.state.employees.items())
            if salaries > 0:
                self.state.money -= salaries
                self.state.daily_expenses += salaries
                self.popup(f"Salários -{money(salaries)}", WIDTH - 260, 110, DANGER)

        self.state.restock_cooldown = max(0.0, self.state.restock_cooldown - dt)
        self._handle_events(dt)
        self._simulate_customers(dt)
        self._simulate_employees(dt)
        self._update_popups(dt)
        self._update_notifications(dt)
        self._check_missions_and_achievements()

        if self.tab == "store":
            self._spawn_customers(dt)

    def _handle_events(self, dt):
        self.event_timer -= dt
        if self.state.event and time.monotonic() >= self.state.event_ends_at:
            self.notify("O evento terminou.", MUTED)
            self.state.event = None
        if self.event_timer <= 0 and self.state.level >= 2 and self.state.event is None:
            self.event_timer = random.uniform(35, 55)
            self.state.event = random.choice(EVENTS).copy()
            self.state.event_ends_at = time.monotonic() + self.state.event["duration"]
            self.notify(self.state.event["title"] + "!", WARNING)

    def _spawn_customers(self, dt):
        self.spawn_timer -= dt
        cap = self.state.max_customers()
        if self.spawn_timer <= 0 and len(self.customers) < cap:
            rush = bool(self.state.event and self.state.event["key"] == "rush")
            self.spawn_timer = random.uniform(1.0, 2.0) if not rush else random.uniform(0.35, 0.8)
            kinds = ["normal", "normal", "apressado", "grande", "economico"]
            kind = random.choice(kinds)
            speed = {"normal": 70, "apressado": 100, "grande": 60, "economico": 78}[kind]
            colors = {
                "normal": (94, 114, 153),
                "apressado": (218, 137, 82),
                "grande": (104, 165, 121),
                "economico": (149, 113, 190),
            }
            target = self._choose_customer_product(kind)
            if target is None:
                return
            self.customers.append(Customer(kind, 90, 510, "enter", target, 1, 0, speed, colors[kind]))

    def _choose_customer_product(self, kind):
        candidates = [k for k in self.state.unlocked if self.state.shelf_stock.get(k, 0) > 0]
        if not candidates:
            return None
        if kind == "economico":
            return min(candidates, key=lambda k: PRODUCTS[k].sell_price)
        if kind == "grande":
            # Cliente compra 2 unidades quando há disponibilidade.
            return random.choice(candidates)
        return random.choice(candidates)

    def _simulate_customers(self, dt):
        store_bounds = self.store_bounds()
        counter = (store_bounds.right - 105, store_bounds.bottom - 90)
        exit_point = (store_bounds.right + 30, store_bounds.bottom - 80)

        for customer in list(self.customers):
            customer.lifetime += dt
            if customer.state == "enter":
                target = (store_bounds.left + 50, store_bounds.bottom - 60)
                self._move_customer(customer, target, dt)
                if self._distance(customer.x, customer.y, *target) < 8:
                    customer.state = "to_product"
                    customer.wait = 0
            elif customer.state == "to_product":
                target_pos = self._product_display_position(customer.target_product, store_bounds)
                self._move_customer(customer, target_pos, dt)
                if self._distance(customer.x, customer.y, *target_pos) < 10:
                    customer.state = "buying"
                    customer.wait = 0
            elif customer.state == "buying":
                customer.wait += dt
                if customer.wait >= (0.55 if self.state.employees["cashier"] else 0.9):
                    self._complete_purchase(customer)
                    customer.state = "to_counter"
            elif customer.state == "to_counter":
                self._move_customer(customer, counter, dt)
                if self._distance(customer.x, customer.y, *counter) < 10:
                    customer.state = "leave"
            elif customer.state == "leave":
                self._move_customer(customer, exit_point, dt)
                if customer.x > store_bounds.right + 10 or customer.lifetime > 30:
                    if customer in self.customers:
                        self.customers.remove(customer)

    def _complete_purchase(self, customer):
        key = customer.target_product
        if not key or self.state.shelf_stock.get(key, 0) <= 0:
            customer.state = "leave"
            self.notify("Um cliente não encontrou o produto.", DANGER)
            return

        qty = 2 if customer.kind == "grande" and self.state.shelf_stock[key] >= 2 else 1
        product = PRODUCTS[key]
        self.state.shelf_stock[key] -= qty
        revenue = product.sell_price * qty
        if self.state.event and self.state.event["key"] == "sale":
            revenue *= 1.5
        self.state.money += revenue
        self.state.revenue += revenue
        self.state.total_sales += qty
        self.state.customers_served += 1
        self.state.xp += revenue * 0.35
        customer.purchased = True
        self.popup(f"+{money(revenue)}", customer.x, customer.y - 22, SUCCESS)
        self.notify(f"Venda: {product.name} +{money(revenue)}", SUCCESS)
        if self.state.shelf_stock[key] == 0:
            self.notify(f"Estoque de {product.name} na prateleira acabou.", WARNING)

        self._unlock_by_level()
        self.state.recalc_level()

    def _unlock_by_level(self):
        before = set(self.state.unlocked)
        self.state.reconcile_unlocks()
        added = set(self.state.unlocked) - before
        for key in added:
            self.notify(f"Novo produto desbloqueado: {PRODUCTS[key].name}!", CYAN)

    def _simulate_employees(self, dt):
        if self.state.employees["stock"] > 0:
            for key in self.state.unlocked:
                if self.state.product_stock[key] > 0 and self.state.shelf_stock[key] < 2:
                    self.state.product_stock[key] -= 1
                    self.state.shelf_stock[key] += 1
                    break

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return math.hypot(x1 - x2, y1 - y2)

    @staticmethod
    def _move_customer(customer, target, dt):
        dx = target[0] - customer.x
        dy = target[1] - customer.y
        d = math.hypot(dx, dy)
        if d > 0:
            step = customer.speed * dt
            customer.x += dx / d * min(step, d)
            customer.y += dy / d * min(step, d)

    def _product_display_position(self, key, bounds):
        keys = list(self.state.unlocked)
        try:
            idx = keys.index(key)
        except ValueError:
            idx = 0
        cols = 4
        col = idx % cols
        row = idx // cols
        x = bounds.left + 90 + col * 165
        y = bounds.top + 120 + row * 105
        return x, y

    def store_bounds(self):
        # Área lógica fixa para caber no layout; a expansão aparece dentro dela
        # por meio de novas zonas, móveis e prateleiras liberadas por nível.
        return pygame.Rect(36, 152, 814, 488)

    def _update_popups(self, dt):
        for item in list(self.popups):
            item.life -= dt
            item.y -= 18 * dt
            if item.life <= 0:
                self.popups.remove(item)

    def _update_notifications(self, dt):
        updated = []
        for msg, color, life in self.notifications:
            life -= dt
            if life > 0:
                updated.append((msg, color, life))
        self.notifications = updated[-5:]

    def _check_missions_and_achievements(self):
        for mission in MISSIONS:
            if mission["key"] in self.state.completed_missions:
                continue
            done = False
            if mission["key"] == "first_sale":
                done = self.state.total_sales >= 1
            elif mission["key"] == "first_profit":
                done = self.state.revenue >= 100
            elif mission["key"] == "level_2":
                done = self.state.level >= 2
            elif mission["key"] == "customers_50":
                done = self.state.customers_served >= 50
            elif mission["key"] == "sales_100":
                done = self.state.total_sales >= 100
            if done:
                self.state.completed_missions.append(mission["key"])
                self.state.money += mission["reward"]
                self.notify(f"Missão concluída: {mission['title']} +{money(mission['reward'])}", SUCCESS)

        achievement_checks = {
            "first_customer": self.state.customers_served >= 1,
            "sales_100": self.state.total_sales >= 100,
            "revenue_1000": self.state.revenue >= 1000,
            "level_3": self.state.level >= 3,
            "products_10": len(self.state.unlocked) >= 10,
            "first_employee": sum(self.state.employees.values()) >= 1,
            "mega_store": self.state.level >= 4,
        }
        for key, done in achievement_checks.items():
            if done and key not in self.state.claimed_achievements:
                self.state.claimed_achievements.append(key)
                self.notify(f"Conquista: {self._achievement_title(key)}", WARNING)

    def _achievement_title(self, key):
        for k, title, _ in ACHIEVEMENTS:
            if k == key:
                return title
        return key

    def save(self):
        ok = self.save_manager.save(self.state.to_dict())
        if ok:
            self.notify("Jogo salvo.", MUTED)
        else:
            self.notify("Não foi possível salvar.", DANGER)

    def reset_save(self):
        self.state = GameState()
        self.customers.clear()
        self.tutorial_overlay = True
        self.tab = "store"
        try:
            if self.save_manager.web:
                self.save_manager.js.window.localStorage.removeItem(SAVE_FILE)
            elif os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            self.notify("Novo jogo iniciado.", CYAN)
        except Exception:
            self.notify("Novo jogo iniciado nesta sessão.", CYAN)

    # ---------- Interação ----------
    def handle_click(self, pos):
        x, y = pos
        if self.tutorial_overlay:
            if pygame.Rect(500, 560, 280, 55).collidepoint(pos):
                self.state.tutorial_done = True
                self.tutorial_overlay = False
                self.save()
            return

        if pygame.Rect(0, 92, 1280, 58).collidepoint(pos):
            if 25 <= x <= 140:
                self.tab = "store"
            elif 150 <= x <= 295:
                self.tab = "stock"
            elif 305 <= x <= 450:
                self.tab = "upgrades"
            elif 460 <= x <= 605:
                self.tab = "employees"
            elif 615 <= x <= 740:
                self.tab = "missions"
            elif 750 <= x <= 895:
                self.tab = "achievements"
            return

        if x >= 1045 and y >= 88 and y <= 132:
            self.save()
            return
        if x >= 1120 and y >= 136 and y <= 180:
            self.reset_save()
            return

        if self.tab == "store":
            self._click_store(pos)
        elif self.tab == "stock":
            self._click_stock(pos)
        elif self.tab == "upgrades":
            self._click_upgrades(pos)
        elif self.tab == "employees":
            self._click_employees(pos)

    def _click_store(self, pos):
        # Clique no painel rápido de compra/repor à direita.
        x, y = pos
        if x > 875:
            rows = self._panel_product_rows()
            for key, rect in rows:
                if pygame.Rect(rect.x, rect.y, rect.w, 48).collidepoint(pos):
                    self.buy_stock(key, 5)
                    return
        # Atalho: clicar no botão de ampliar prateleiras visível no mapa.
        if pygame.Rect(480, 540, 135, 42).collidepoint(pos):
            self.try_upgrade("shelves")

    def _click_stock(self, pos):
        rows = self._panel_product_rows(stock=True)
        for key, rect in rows:
            if pygame.Rect(rect.x, rect.y, rect.w, 48).collidepoint(pos):
                # Primeiro botão compra estoque, segundo repõe na prateleira.
                if pos[0] < rect.x + rect.w * 0.55:
                    self.buy_stock(key, 5)
                else:
                    self.shelve_product(key, 5)
                return

    def _click_upgrades(self, pos):
        cards = self._upgrade_cards()
        for key, rect in cards:
            if rect.collidepoint(pos):
                self.try_upgrade(key)
                return

    def _click_employees(self, pos):
        cards = self._employee_cards()
        for key, rect in cards:
            if rect.collidepoint(pos):
                self.hire_employee(key)
                return

    def buy_stock(self, key, amount=5):
        if key not in self.state.unlocked:
            self.notify("Esse produto ainda está bloqueado.", DANGER)
            return
        product = PRODUCTS[key]
        discount = 0.65 if self.state.event and self.state.event["key"] == "supplier" else 1.0
        price = product.buy_price * amount * discount
        capacity = self.state.warehouse_capacity(key)
        if self.state.product_stock[key] + amount > capacity:
            self.notify(f"Capacidade máxima: {capacity} unidades.", WARNING)
            return
        if self.state.money < price:
            self.notify("Dinheiro insuficiente.", DANGER)
            return
        self.state.money -= price
        self.state.product_stock[key] += amount
        self.popup(f"+{amount} {product.name}", 965, 235, CYAN)
        if self.state.tutorial_step == 0:
            self.state.tutorial_step = 1

    def shelve_product(self, key, amount=5):
        if key not in self.state.unlocked:
            return
        free_slots = max(0, self.state.max_shelf_slots() - sum(self.state.shelf_stock.values()))
        amount = min(amount, free_slots, self.state.product_stock[key])
        if amount <= 0:
            self.notify("Não há espaço ou estoque para colocar na prateleira.", WARNING)
            return
        self.state.product_stock[key] -= amount
        self.state.shelf_stock[key] += amount
        self.notify(f"{amount}x {PRODUCTS[key].name} colocado na prateleira.", CYAN)
        if self.state.tutorial_step == 1:
            self.state.tutorial_step = 2

    def try_upgrade(self, key):
        level = self.state.upgrades[key]
        info = UPGRADES[key]
        cost = info["base"] + level * info["step"]
        if key == "space" and self.state.level < 2:
            self.notify("Mais espaço fica disponível no nível 2.", WARNING)
            return
        if key == "entrance" and self.state.level < 2:
            self.notify("Entrada maior fica disponível no nível 2.", WARNING)
            return
        if self.state.money < cost:
            self.notify("Dinheiro insuficiente para esse upgrade.", DANGER)
            return
        self.state.money -= cost
        self.state.upgrades[key] += 1
        self.notify(f"Upgrade comprado: {info['name']}!", SUCCESS)
        self.save()

    def hire_employee(self, key):
        info = EMPLOYEES[key]
        if self.state.level < 2:
            self.notify("Funcionários são liberados no nível 2.", WARNING)
            return
        if self.state.money < info["cost"]:
            self.notify("Dinheiro insuficiente para contratar.", DANGER)
            return
        if self.state.employees[key] >= 3:
            self.notify("Limite inicial de 3 funcionários dessa função.", WARNING)
            return
        self.state.money -= info["cost"]
        self.state.employees[key] += 1
        self.notify(f"{info['name']} contratado!", SUCCESS)
        self.save()

    # ---------- UI ----------
    def draw(self):
        canvas = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        canvas.fill(BG)
        self._draw_header(canvas)
        self._draw_nav(canvas)

        if self.tab == "store":
            self._draw_store(canvas)
        elif self.tab == "stock":
            self._draw_stock(canvas)
        elif self.tab == "upgrades":
            self._draw_upgrades(canvas)
        elif self.tab == "employees":
            self._draw_employees(canvas)
        elif self.tab == "missions":
            self._draw_missions(canvas)
        elif self.tab == "achievements":
            self._draw_achievements(canvas)

        self._draw_notifications(canvas)
        self._draw_tutorial(canvas)

        scale, ox, oy = self.resize_scale()
        scaled = pygame.transform.smoothscale(canvas, (int(WIDTH * scale), int(HEIGHT * scale)))
        self.screen.fill(BG)
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    def _draw_header(self, surface):
        draw_round_rect(surface, pygame.Rect(0, 0, WIDTH, 92), PANEL, 0)
        text(surface, self.fonts["title"], "LOJA DO ZERO", (25, 20), PRIMARY)
        text(surface, self.fonts["small"], LEVELS[self.state.level][0], (29, 67), MUTED)

        cards = [
            ("DINHEIRO", money(self.state.money), SUCCESS, 320),
            ("NÍVEL", f"{self.state.level}/5", PRIMARY, 500),
            ("SATISFAÇÃO", f"{self.state.satisfaction()}%", CYAN, 670),
            ("CLIENTES", str(len(self.customers)), WARNING, 850),
        ]
        for title_label, value, color, x in cards:
            draw_round_rect(surface, pygame.Rect(x, 16, 155, 60), (247, 248, 251), 12)
            text(surface, self.fonts["tiny"], title_label, (x + 12, 26), MUTED)
            text(surface, self.fonts["medium"], value, (x + 12, 46), color)

        draw_round_rect(surface, pygame.Rect(1015, 18, 110, 50), PRIMARY, 12)
        text(surface, self.fonts["small"], "SALVAR", (1070, 43), WHITE, "center")
        draw_round_rect(surface, pygame.Rect(1138, 18, 115, 50), (234, 235, 240), 12)
        text(surface, self.fonts["small"], "NOVO JOGO", (1195, 43), INK, "center")

    def _draw_nav(self, surface):
        items = [
            ("store", "LOJA", 25, 115),
            ("stock", "ESTOQUE", 150, 115),
            ("upgrades", "MELHORIAS", 305, 115),
            ("employees", "FUNCIONÁRIOS", 460, 115),
            ("missions", "MISSÕES", 615, 115),
            ("achievements", "CONQUISTAS", 750, 115),
        ]
        for tab, label, x, y in items:
            active = tab == self.tab
            rect = pygame.Rect(x, y - 23, 132 if tab not in ("employees", "achievements") else 150, 42)
            draw_round_rect(surface, rect, PRIMARY if active else PANEL, 10)
            text(surface, self.fonts["small"], label, rect.center, WHITE if active else MUTED, "center")

    def _draw_store(self, surface):
        bounds = self.store_bounds()
        draw_round_rect(surface, bounds, FLOOR, 18)
        pygame.draw.rect(surface, WALL, pygame.Rect(bounds.left, bounds.top, bounds.w, 18), border_radius=18)
        text(surface, self.fonts["small"], "ÁREA DA LOJA", (bounds.left + 16, bounds.top + 24), MUTED)
        # Novas áreas visuais indicam a expansão da loja sem exigir um mapa gigantesco.
        if self.state.level >= 2:
            pygame.draw.rect(surface, (235, 239, 246), pygame.Rect(bounds.left + 14, bounds.top + 55, 785, 360), 2, border_radius=12)
        if self.state.level >= 3:
            pygame.draw.rect(surface, (226, 240, 235), pygame.Rect(bounds.left + 270, bounds.top + 55, 250, 360), 2, border_radius=12)
        if self.state.level >= 4:
            pygame.draw.rect(surface, (241, 232, 247), pygame.Rect(bounds.left + 520, bounds.top + 55, 250, 360), 2, border_radius=12)

        # Entrada, caixa e prateleiras.
        entrance = pygame.Rect(bounds.left + 16, bounds.bottom - 74, 100, 55)
        draw_round_rect(surface, entrance, (210, 227, 219), 10)
        text(surface, self.fonts["small"], "ENTRADA", entrance.center, SUCCESS, "center")

        counter = pygame.Rect(bounds.right - 145, bounds.bottom - 88, 115, 52)
        draw_round_rect(surface, counter, WOOD, 10)
        text(surface, self.fonts["tiny"], "CAIXA", counter.center, WHITE, "center")

        keys = list(self.state.unlocked)
        cols = 4
        for idx, key in enumerate(keys):
            col, row = idx % cols, idx // cols
            x = bounds.left + 36 + col * 175
            y = bounds.top + 70 + row * 105
            rect = pygame.Rect(x, y, 145, 78)
            draw_round_rect(surface, rect, WHITE, 12)
            pygame.draw.rect(surface, PRODUCTS[key].color, pygame.Rect(rect.x, rect.y, rect.w, 8), border_radius=8)
            text(surface, self.fonts["small"], PRODUCTS[key].name, (rect.x + 10, rect.y + 16), INK)
            text(surface, self.fonts["tiny"], f"Prateleira: {self.state.shelf_stock[key]}", (rect.x + 10, rect.y + 44), MUTED)
            text(surface, self.fonts["tiny"], f"Venda {money(PRODUCTS[key].sell_price)}", (rect.x + 10, rect.y + 61), SUCCESS)

        # Clientes.
        for customer in self.customers:
            pygame.draw.circle(surface, customer.color, (int(customer.x), int(customer.y)), 10)
            pygame.draw.circle(surface, WHITE, (int(customer.x - 3), int(customer.y - 3)), 2)

        # Painel lateral.
        panel = pygame.Rect(875, 152, 370, 488)
        draw_round_rect(surface, panel, PANEL, 18)
        text(surface, self.fonts["large"], "Operação", (900, 175), INK)
        text(surface, self.fonts["small"], "Compre estoque e abasteça as prateleiras.", (900, 216), MUTED)
        self._draw_event(surface, panel)

        text(surface, self.fonts["medium"], "Compra rápida", (900, 280), PRIMARY)
        for key, rect in self._panel_product_rows():
            draw_round_rect(surface, rect, (247, 248, 251), 10)
            text(surface, self.fonts["small"], PRODUCTS[key].name, (rect.x + 12, rect.y + 9), INK)
            text(surface, self.fonts["tiny"], f"Estoque {self.state.product_stock[key]}", (rect.x + 12, rect.y + 29), MUTED)
            draw_round_rect(surface, pygame.Rect(rect.right - 92, rect.y + 7, 78, 34), PRIMARY, 8)
            text(surface, self.fonts["tiny"], f"+5 / {money(PRODUCTS[key].buy_price * 5)}", (rect.right - 53, rect.y + 24), WHITE, "center")

        upgrade_hint = pygame.Rect(900, 570, 300, 50)
        draw_round_rect(surface, upgrade_hint, (246, 247, 251), 12)
        text(surface, self.fonts["tiny"], "Meta do próximo nível", (upgrade_hint.x + 12, upgrade_hint.y + 9), MUTED)
        target = self.state.next_level_target()
        label = "NÍVEL MÁXIMO" if self.state.level >= 5 else f"Faturamento: {money(self.state.revenue)} / {money(target)}"
        text(surface, self.fonts["small"], label, (upgrade_hint.x + 12, upgrade_hint.y + 28), PRIMARY)

    def _draw_event(self, surface, panel):
        if not self.state.event:
            draw_round_rect(surface, pygame.Rect(panel.x + 25, 245, 320, 26), (247, 248, 251), 8)
            text(surface, self.fonts["tiny"], "Nenhum evento ativo", (panel.x + 185, 258), MUTED, "center")
            return
        remaining = max(0, int(self.state.event_ends_at - time.monotonic()))
        rect = pygame.Rect(panel.x + 25, 245, 320, 54)
        draw_round_rect(surface, rect, (255, 246, 218), 10)
        text(surface, self.fonts["small"], f"{self.state.event['title']}  ({remaining}s)", (rect.x + 10, rect.y + 7), WARNING)
        text(surface, self.fonts["tiny"], self.state.event["message"], (rect.x + 10, rect.y + 29), INK)

    def _panel_product_rows(self, stock=False):
        rows = []
        y0 = 315
        for i, key in enumerate(self.state.unlocked[:7]):
            rect = pygame.Rect(900, y0 + i * 48, 320, 42)
            rows.append((key, rect))
        return rows

    def _draw_stock(self, surface):
        text(surface, self.fonts["title"], "Estoque", (35, 170), INK)
        text(surface, self.fonts["small"], "Compre no depósito e coloque os itens na área de venda.", (38, 218), MUTED)
        headers = [(60, "PRODUTO"), (290, "DEPÓSITO"), (455, "PRATELEIRA"), (625, "COMPRA"), (760, "VENDA"), (915, "AÇÃO")]
        for x, label in headers:
            text(surface, self.fonts["tiny"], label, (x, 260), MUTED)
        for i, key in enumerate(self.state.unlocked):
            y = 285 + i * 42
            if y > 620:
                break
            draw_round_rect(surface, pygame.Rect(40, y - 5, 850, 36), PANEL, 8)
            text(surface, self.fonts["small"], PRODUCTS[key].name, (60, y + 5), INK)
            text(surface, self.fonts["small"], str(self.state.product_stock[key]), (300, y + 5), PRIMARY)
            shelf = self.state.shelf_stock[key]
            color = WARNING if shelf <= 1 else SUCCESS
            text(surface, self.fonts["small"], str(shelf), (465, y + 5), color)
            text(surface, self.fonts["tiny"], money(PRODUCTS[key].buy_price), (625, y + 6), MUTED)
            text(surface, self.fonts["tiny"], money(PRODUCTS[key].sell_price), (760, y + 6), SUCCESS)
            draw_round_rect(surface, pygame.Rect(815, y - 2, 105, 30), PRIMARY, 8)
            text(surface, self.fonts["tiny"], "COMPRAR +5", (867, y + 13), WHITE, "center")
            draw_round_rect(surface, pygame.Rect(930, y - 2, 125, 30), CYAN, 8)
            text(surface, self.fonts["tiny"], "REPOR +5", (992, y + 13), WHITE, "center")

        side = pygame.Rect(915, 170, 310, 105)
        cap = self.state.warehouse_capacity(self.state.unlocked[0])
        draw_round_rect(surface, side, PANEL, 14)
        text(surface, self.fonts["medium"], "Capacidade", (935, 188), PRIMARY)
        text(surface, self.fonts["small"], f"Até {cap} unidades / produto", (935, 225), INK)
        text(surface, self.fonts["tiny"], "Aumente em MELHORIAS.", (935, 252), MUTED)

    def _upgrade_cards(self):
        cards = []
        keys = list(UPGRADES.keys())
        for i, key in enumerate(keys):
            col = i % 2
            row = i // 2
            rect = pygame.Rect(45 + col * 430, 245 + row * 125, 390, 105)
            cards.append((key, rect))
        return cards

    def _draw_upgrades(self, surface):
        text(surface, self.fonts["title"], "Melhorias", (35, 170), INK)
        text(surface, self.fonts["small"], "Invista na estrutura para vender mais e atender melhor.", (38, 218), MUTED)
        for key, rect in self._upgrade_cards():
            info = UPGRADES[key]
            level = self.state.upgrades[key]
            cost = info["base"] + level * info["step"]
            affordable = self.state.money >= cost
            draw_round_rect(surface, rect, PANEL, 16)
            draw_round_rect(surface, pygame.Rect(rect.x + 15, rect.y + 15, 52, 52), (243, 244, 249), 12)
            text(surface, self.fonts["medium"], str(level), (rect.x + 41, rect.y + 41), PRIMARY, "center")
            text(surface, self.fonts["medium"], info["name"], (rect.x + 82, rect.y + 18), INK)
            text(surface, self.fonts["tiny"], info["desc"], (rect.x + 82, rect.y + 49), MUTED)
            draw_round_rect(surface, pygame.Rect(rect.right - 112, rect.bottom - 42, 96, 30), SUCCESS if affordable else (198, 201, 209), 8)
            text(surface, self.fonts["tiny"], money(cost), (rect.right - 64, rect.bottom - 27), WHITE if affordable else INK, "center")

    def _employee_cards(self):
        cards = []
        for i, key in enumerate(EMPLOYEES):
            rect = pygame.Rect(45, 250 + i * 120, 900, 100)
            cards.append((key, rect))
        return cards

    def _draw_employees(self, surface):
        text(surface, self.fonts["title"], "Funcionários", (35, 170), INK)
        text(surface, self.fonts["small"], "A partir do nível 2, sua equipe começa a automatizar a operação.", (38, 218), MUTED)
        for key, rect in self._employee_cards():
            info = EMPLOYEES[key]
            count = self.state.employees[key]
            can = self.state.money >= info["cost"] and self.state.level >= 2 and count < 3
            draw_round_rect(surface, rect, PANEL, 16)
            draw_round_rect(surface, pygame.Rect(rect.x + 18, rect.y + 17, 70, 65), (244, 245, 249), 12)
            text(surface, self.fonts["medium"], str(count), (rect.x + 53, rect.y + 49), PRIMARY, "center")
            text(surface, self.fonts["large"], info["name"], (rect.x + 110, rect.y + 17), INK)
            text(surface, self.fonts["small"], info["benefit"], (rect.x + 112, rect.y + 55), MUTED)
            draw_round_rect(surface, pygame.Rect(rect.right - 175, rect.y + 23, 145, 50), SUCCESS if can else (202, 204, 212), 10)
            label = f"CONTRATAR {money(info['cost'])}"
            if count >= 3:
                label = "LIMITE 3"
            elif self.state.level < 2:
                label = "NÍVEL 2"
            text(surface, self.fonts["tiny"], label, (rect.right - 102, rect.y + 48), WHITE if can else INK, "center")
        text(surface, self.fonts["small"], "Salários são descontados a cada 30 segundos.", (45, 620), MUTED)

    def _draw_missions(self, surface):
        text(surface, self.fonts["title"], "Missões", (35, 170), INK)
        text(surface, self.fonts["small"], "Objetivos curtos ajudam sua loja a crescer passo a passo.", (38, 218), MUTED)
        for i, mission in enumerate(MISSIONS):
            y = 255 + i * 72
            done = mission["key"] in self.state.completed_missions
            draw_round_rect(surface, pygame.Rect(45, y, 900, 58), PANEL if not done else (231, 247, 239), 12)
            text(surface, self.fonts["small"], mission["title"], (65, y + 10), SUCCESS if done else INK)
            text(surface, self.fonts["tiny"], mission["desc"], (65, y + 34), MUTED)
            text(surface, self.fonts["small"], f"+{money(mission['reward'])}", (860, y + 28), SUCCESS if done else WARNING, "center")
            text(surface, self.fonts["tiny"], "CONCLUÍDA" if done else "EM ANDAMENTO", (780, y + 28), SUCCESS if done else MUTED, "center")

    def _draw_achievements(self, surface):
        text(surface, self.fonts["title"], "Conquistas", (35, 170), INK)
        text(surface, self.fonts["small"], "Colecione marcos enquanto sua loja ganha escala.", (38, 218), MUTED)
        for i, (key, title_label, desc) in enumerate(ACHIEVEMENTS):
            col = i % 2
            row = i // 2
            rect = pygame.Rect(45 + col * 455, 255 + row * 82, 420, 68)
            done = key in self.state.claimed_achievements
            draw_round_rect(surface, rect, (231, 247, 239) if done else PANEL, 12)
            badge = SUCCESS if done else (201, 204, 213)
            pygame.draw.circle(surface, badge, (rect.x + 34, rect.centery), 17)
            text(surface, self.fonts["small"], "OK" if done else "?", (rect.x + 34, rect.centery), WHITE if done else MUTED, "center")
            text(surface, self.fonts["small"], title_label, (rect.x + 65, rect.y + 12), INK)
            text(surface, self.fonts["tiny"], desc, (rect.x + 65, rect.y + 38), MUTED)

    def _draw_notifications(self, surface):
        y = 155
        for msg, color, life in reversed(self.notifications):
            width = min(480, max(240, self.fonts["small"].size(msg)[0] + 40))
            x = WIDTH - width - 28
            draw_round_rect(surface, pygame.Rect(x, y, width, 36), PANEL, 10)
            pygame.draw.circle(surface, color, (x + 16, y + 18), 5)
            text(surface, self.fonts["tiny"], msg, (x + 30, y + 10), INK)
            y += 42

        for item in self.popups:
            alpha = int(255 * clamp(item.life / 1.25, 0, 1))
            image = self.fonts["small"].render(item.message, True, item.color)
            image.set_alpha(alpha)
            surface.blit(image, (int(item.x), int(item.y)))

    def _draw_tutorial(self, surface):
        if self.state.tutorial_done and self.tutorial_overlay is False:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 150))
        surface.blit(overlay, (0, 0))
        box = pygame.Rect(320, 145, 640, 500)
        draw_round_rect(surface, box, PANEL, 20)
        text(surface, self.fonts["title"], "Bem-vindo à Loja do Zero!", (box.centerx, box.y + 55), PRIMARY, "center")
        text(surface, self.fonts["body"], "Comece pequeno, venda bastante e", (box.centerx, box.y + 118), INK, "center")
        text(surface, self.fonts["body"], "transforme sua lojinha em um grande negócio.", (box.centerx, box.y + 148), INK, "center")

        steps = [
            ("1", "Compre 5 unidades de um produto."),
            ("2", "Abra ESTOQUE e coloque os produtos na prateleira."),
            ("3", "Espere o cliente comprar e acompanhe o dinheiro."),
            ("4", "Use os ganhos em MELHORIAS e FUNCIONÁRIOS."),
        ]
        for i, (number, label) in enumerate(steps):
            y = box.y + 215 + i * 58
            pygame.draw.circle(surface, PRIMARY, (box.x + 65, y), 17)
            text(surface, self.fonts["small"], number, (box.x + 65, y), WHITE, "center")
            text(surface, self.fonts["small"], label, (box.x + 100, y - 10), INK)

        draw_round_rect(surface, pygame.Rect(500, 560, 280, 55), PRIMARY, 12)
        text(surface, self.fonts["medium"], "COMEÇAR", (640, 588), WHITE, "center")

    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Janela redimensionável; a renderização usa escala lógica.
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(self.logical_mouse())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_F5:
                        self.save()
                    elif event.key == pygame.K_F2:
                        self.reset_save()

            self.update(dt)
            self.draw()
            await asyncio.sleep(0)

        self.save()
        pygame.quit()


async def main():
    game = ShopGame()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
