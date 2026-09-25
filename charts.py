import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import numpy as np

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

BG     = '#0e1116'
CARD   = '#1a1f27'
GREEN  = '#4CAF50'
BLUE   = '#2196F3'
RED    = '#E53935'
GOLD   = '#FFC107'
TEXT   = '#E8EAED'
MUTED  = '#8A8F98'
ORANGE = '#FF7043'


def draw_circle(percent, label, value_text, color=BLUE, size=6):
    percent = max(0, min(100, percent))
    fig, ax = plt.subplots(figsize=(size, size), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

    ax.add_patch(Circle((0, 0), 1.0, color=CARD, zorder=1))
    ax.add_patch(Wedge((0, 0), 0.95, 90, 90 - 360, width=0.18,
                       facecolor='#2a2f38', zorder=2))
    angle = 360 * percent / 100
    ax.add_patch(Wedge((0, 0), 0.95, 90, 90 - angle, width=0.18,
                       facecolor=color, zorder=3))

    ax.text(0, 0.08, f'{int(percent)}%', ha='center', va='center',
            fontsize=34, color=TEXT, fontweight='bold', zorder=4)
    ax.text(0, -0.28, label, ha='center', va='center',
            fontsize=13, color=MUTED, zorder=4)
    ax.text(0, -0.55, value_text, ha='center', va='center',
            fontsize=11, color=color, zorder=4, fontweight='bold')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.15)
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_week_chart(water_pct_list, food_pct_list, days=None):
    if days is None:
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(days))
    w = 0.38
    ax.bar(x - w/2, water_pct_list, w, label='💧 Вода',
           color=BLUE, edgecolor='none')
    ax.bar(x + w/2, food_pct_list, w, label='🍎 Еда',
           color=GREEN, edgecolor='none')
    ax.axhline(100, color=GOLD, linestyle='--', linewidth=1, alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(days, color=TEXT, fontsize=11)
    ax.set_ylim(0, 120)
    ax.set_ylabel('% от нормы', color=TEXT, fontsize=11)
    ax.tick_params(axis='y', colors=TEXT)
    ax.tick_params(axis='x', colors=TEXT)
    for spine in ax.spines.values():
        spine.set_color('#2a2f38')
    ax.grid(axis='y', color='#2a2f38', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(facecolor=CARD, edgecolor='none', labelcolor=TEXT,
              fontsize=11, loc='upper right')
    ax.set_title('За неделю, бро 🦍', color=TEXT,
                 fontsize=15, fontweight='bold', pad=15)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.2)
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_profile_progress(values, days_since_start, streak=0):
    fig, ax = plt.subplots(figsize=(7, 3.8), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(1, days_since_start + 1) if days_since_start > 0 else np.array([1])
    if not values:
        values = [0] * len(x)
    ax.plot(x, values, color=GREEN, linewidth=2.5, marker='o',
            markersize=5, markerfacecolor=GOLD, markeredgecolor=GREEN)
    ax.fill_between(x, values, color=GREEN, alpha=0.15)
    ax.set_ylim(-5, 110)
    ax.set_xlim(0.5, max(len(x) + 0.5, 7))
    ax.set_xlabel('День', color=TEXT, fontsize=11)
    ax.set_ylabel('Прогресс %', color=TEXT, fontsize=11)
    ax.tick_params(axis='both', colors=TEXT)
    for spine in ax.spines.values():
        spine.set_color('#2a2f38')
    ax.grid(color='#2a2f38', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title(f'Прогресс, бро 🦍  |  🔥 {streak} дней',
                 color=TEXT, fontsize=14, fontweight='bold', pad=12)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.2)
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_nofap_stats(week_values, days=None, total=0, today=0):
    if days is None:
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(days))
    colors = [GREEN if v == 0 else (GOLD if v <= 2 else RED) for v in week_values]
    bars = ax.bar(x, week_values, color=colors, edgecolor='none', width=0.55)
    for bar, v in zip(bars, week_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(v), ha='center', color=TEXT, fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(days, color=TEXT, fontsize=11)
    ax.tick_params(axis='y', colors=TEXT)
    for spine in ax.spines.values():
        spine.set_color('#2a2f38')
    ax.grid(axis='y', color='#2a2f38', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title(f'📊 Сегодня: {today}  |  Всего: {total}',
                 color=TEXT, fontsize=14, fontweight='bold', pad=12)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.2)
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_strength_card(exercise, weight, emoji_items):
    fig, ax = plt.subplots(figsize=(6, 4), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis('off')
    ax.text(0.5, 0.88, f'💪 {exercise}', ha='center', va='center',
            fontsize=20, color=GOLD, fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.70, f'{weight} кг', ha='center', va='center',
            fontsize=36, color=TEXT, fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.58, 'Это как:', ha='center', va='center',
            fontsize=13, color=MUTED, transform=ax.transAxes)
    y = 0.42
    for item in emoji_items:
        ax.text(0.5, y, item, ha='center', va='center',
                fontsize=14, color=TEXT, transform=ax.transAxes)
        y -= 0.12
    ax.text(0.5, 0.08, 'Ты красавчик, бро 🦍', ha='center', va='center',
            fontsize=13, color=GREEN, fontweight='bold', transform=ax.transAxes)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.2)
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_title_card(title, emoji, reason):
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis('off')
    ax.text(0.5, 0.80, '🏅 Титул дня', ha='center', va='center',
            fontsize=13, color=MUTED, transform=ax.transAxes)
    ax.text(0.5, 0.55, f'{emoji} {title}', ha='center', va='center',
            fontsize=28, color=GOLD, fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.25, reason, ha='center', va='center',
            fontsize=12, color=TEXT, transform=ax.transAxes, wrap=True)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=BG,
                bbox_inches='tight', pad_inches=0.2)
    buf.seek(0)
    plt.close(fig)
    return buf
