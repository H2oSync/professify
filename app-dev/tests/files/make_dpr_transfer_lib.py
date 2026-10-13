#!/usr/bin/env python3
"""The synthetic report drawing code, shared by make-dpr-transfer.py and make-dpr-stress.py (split out 2026-10-11)."""
import os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw

W, H = letter

# ---- the icons: small RGBA pictures, each different (the app tells them apart by their pixels) ----
def icon(kind, big=False):
    n = 11 if kind == 'no' else 16
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 'ok':     d.ellipse([1, 1, 14, 14], fill=(122, 190, 92, 255), outline=(52, 110, 40, 255)); d.line([(4, 8), (7, 11), (12, 4)], fill=(30, 70, 25, 255), width=2)
    elif kind == 'no':   d.rectangle([1, 1, 9, 9], fill=(211, 32, 40, 255))
    elif kind == 'ip':   d.polygon([(8, 1), (15, 8), (8, 15), (1, 8)], fill=(244, 196, 64, 255), outline=(190, 140, 30, 255))
    elif kind == 'plan': d.polygon([(8, 1), (10, 6), (15, 6), (11, 10), (12, 15), (8, 12), (4, 15), (5, 10), (1, 6), (6, 6)], fill=(90, 130, 210, 255))
    elif kind == 'xfer': d.polygon([(1, 8), (7, 2), (7, 5), (15, 5), (15, 11), (7, 11), (7, 14)], fill=(150, 210, 130, 255), outline=(60, 130, 50, 255))
    elif kind == 'xfer2': d.polygon([(1, 8), (7, 2), (7, 5), (15, 5), (15, 11), (7, 11), (7, 14)], fill=(151, 210, 130, 255), outline=(60, 130, 50, 255))  # one colour unit off
    elif kind == 'exc':  d.polygon([(8, 1), (15, 14), (1, 14)], fill=(150, 120, 190, 255))
    elif kind == 'what': d.ellipse([2, 2, 13, 13], outline=(90, 110, 140, 255), width=2)
    if big: im = im.resize((80, 80), Image.NEAREST)   # a picture too big to be an icon: the app can't match it
    return ImageReader(im)
ICONS = {k: icon(k) for k in ['ok', 'no', 'ip', 'plan', 'xfer', 'xfer2', 'exc', 'what']}
BIG_OK = icon('ok', big=True)

class Report:
    """Draw-ops are collected per page first, so "Page n of N" is right."""
    def __init__(s, who, emplid, printed, objective, catalog, icons=True, big_ok=False, legend_xfer='xfer'):
        s.who, s.emplid, s.printed, s.icons, s.big_ok = who, emplid, printed, icons, big_ok
        s.pages, s.ops, s.y = [], [], 0
        s.new_page(first=True)
        s.text("Degree Progress Report", W / 2, size=13, bold=True, center=True); s.y -= 15
        s.text("For " + who, W / 2, size=10, center=True); s.y -= 26
        s.text("Current Academic Objective", 90, bold=True); s.text("Requirement (Catalog) Term", 430, bold=True); s.y -= 18
        s.text(objective, 54, bold=True); s.text(catalog, 465, bold=True); s.y -= 34
        s.text("Degree Audit Icons", 140, size=8, bold=True); s.text("Course Icons", 445, size=8, bold=True); s.y -= 16
        for l, li, r, ri in [("Requirement Satisfied", 'ok', "Cal Poly Graded Course", 'ok'), ("Requirement Not Satisfied", 'no', "Course In Progress", 'ip'),
                             ("In Progress", 'ip', "Planned", 'plan'), ("Planned", 'plan', "Transfer/Test/Other Credit", legend_xfer), ("Exception Made", 'exc', "What-If Course", 'what')]:
            s.img(li, 44, 11.9); s.text(l, 66, size=8); s.img(ri, 314, 11.9); s.text(r, 338, size=8); s.y -= 11.9
        s.y -= 18; s.text("DEGREE PROGRESS REPORT", 36, size=10, bold=True); s.y -= 10; s.text("*" * 29, 36, size=6); s.y -= 18
    def new_page(s, first=False):
        if s.ops: s.pages.append(s.ops)
        s.ops = []; s.y = H - 50
        s.ops.append(('furn',))
        s.y = H - 110
    def need(s, h):
        if s.y - h < 50: s.new_page()
    def text(s, t, x, size=8, bold=False, center=False):
        s.ops.append(('text', t, x, s.y, size, bold, center))
    def img(s, kind, x, size, dy=None):
        # an icon's centre sits 1.8pt above its line's baseline, as on the real report
        if s.icons and kind: s.ops.append(('img', kind, x, s.y + (1.8 - size / 2 if dy is None else dy), size))
    # --- requirement blocks ---
    def head(s, t, x=36, size=9):
        s.need(60); s.text(t, x, size=size); s.y -= 12
    def verdict(s, v, words='', more=(), code=None, x=40, units=None, courses=None, used=None):
        s.need(40)
        icon_k = {'S': 'ok', 'N': 'no', 'OS': 'ok', 'ON': 'no', 'IP': 'ip'}[v]
        lab = {'S': 'Satisfied:', 'N': 'Not Satisfied:', 'OS': 'Overall Requirement Satisfied:', 'ON': 'Overall Requirement Not Satisfied:', 'IP': 'In Progress:'}[v]
        s.text(lab, x, bold=True)
        if words: s.text(words, x + (4.6 * len(lab)), size=8)
        s.img(icon_k if icon_k != 'no' else 'no', 565 if icon_k != 'no' else 568, 11.4 if icon_k != 'no' else 8, dy=-2.5)
        s.y -= 10
        for m in more: s.text(m, x, size=8); s.y -= 10
        if code: s.text(code, x, size=8); s.y -= 14
        if units: s.text("· Units: " + units, 54); s.y -= 14
        if courses: s.text("· Courses: " + courses, 54); s.y -= 14
        if used: s.table(used)
        s.y -= 4
    def table(s, rows):
        s.need(30 + 12 * len(rows))
        s.text("Courses Used", W / 2, size=8, bold=True, center=True); s.y -= 18
        for t, x in [("Term", 44), ("Subject", 112), ("Catalog Nbr", 180), ("Course Title", 247), ("Grade", 387), ("Units", 422), ("Requirement", 471), ("Status", 540)]:
            s.text(t, x, bold=True)
        s.y -= 9; s.text("Designation", 471, bold=True); s.y -= 12
        for r in rows:
            term, subj, nbr, title, grade, units, desig, ic = r
            s.text(term, 44); s.text(subj, 112); s.text(nbr, 180); s.text(title, 247)
            if grade: s.text(grade, 387)
            s.text(units, 422)
            if desig: s.text(desig, 471)
            s.img(ic, 553, 11.4); s.y -= 12
        s.y -= 8
    def history(s, rows):
        s.need(80); s.y -= 10
        s.text("Course History", W / 2, size=10, bold=True, center=True); s.y -= 20
        for t, x in [("Term", 44), ("Subject", 133), ("Catalog Nbr", 205), ("Title", 281), ("Grade", 435), ("Units", 478), ("Status", 532)]:
            s.text(t, x, bold=True)
        s.y -= 12
        for r in rows:
            s.need(14)
            if r[0] == 'designation': s.text("Requirement Designation: " + r[1], 48, bold=False); s.y -= 11.4; continue
            term, subj, nbr, title, grade, units, ic = r
            s.text(term, 44); s.text(subj, 133); s.text(nbr, 205); s.text(title, 281)
            if grade: s.text(grade, 435)
            s.text(units, 478); s.img(ic, 547, 11.4); s.y -= 11.4
    def save(s, path):
        s.pages.append(s.ops)
        c = canvas.Canvas(path, pagesize=letter); c.setTitle('Degree Progress Report (synthetic test fixture)'); N = len(s.pages)
        for n, ops in enumerate(s.pages, 1):
            for op in ops:
                if op[0] == 'furn':
                    c.setFont('Helvetica', 8); c.drawRightString(W - 36, H - 40, f"Page {n} of {N}")
                    c.drawRightString(W - 36, H - 72, f"Name: {s.who}"); c.drawRightString(W - 36, H - 82, f"EMPLID: {s.emplid}")
                    c.drawRightString(W - 36, H - 92, f"Date Printed: {s.printed}")
                elif op[0] == 'text':
                    _, t, x, y, size, bold, center = op
                    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
                    (c.drawCentredString if center else c.drawString)(x, y, t)
                elif op[0] == 'img':
                    _, kind, x, y, size = op
                    c.drawImage(BIG_OK if kind == 'ok' and s.big_ok else ICONS[kind], x, y, width=size, height=size, mask='auto')
            c.showPage()
        c.save()

def courses(req, used, need=None):
    return f"{req:.2f} required, {used:.2f} used" + (f", {need:.2f} needed" if need is not None else '')
