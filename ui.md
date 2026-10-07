# Resume Studio — Ivory & Juicy Blackberries UI Design System

This document outlines the **Resume Studio** design system, featuring the modern, high-contrast dual palette of **Ivory (`#EDEBE7`)** and **Juicy Blackberries (`#434451`)**, structured with tailored **`rounded-lg` (8px)** corners (crisp, non-bubbly, non-square) and high-contrast typography.

---

## 🎨 1. Palette & Design Tokens

### Core Colors

| Palette | Hex Code | RGB | Tone | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Ivory** | `#EDEBE7` | `237, 235, 231` | Primary Canvas Background | Main page background canvas & solid container surfaces |
| **Juicy Blackberries** | `#434451` | `67, 68, 81` | Primary Brand Accent | Buttons, active icons, status highlights, borders, focus rings |
| **Blackberry Deep** | `#25262E` | `37, 38, 46` | Primary Typography & Dark State | Headers, body text, high-contrast button hover |
| **Ivory Subtle** | `#DFDCD5` | `223, 220, 213` | Accent Containers | Inner cards, table headers, active badges |
| **Muted Slate** | `#626372` | `98, 99, 114` | Secondary Typography | Subtitles, labels, secondary metadata |

---

## 🧩 2. Design Principles

1. **Crisp 8px Corners (`rounded-lg`)**: No bubbly `rounded-2xl` / `rounded-full` pills, and no 90° square boxes. Clean, tailored modern corners throughout.
2. **Solid Defined Contrast**: Pure solid colors with strong defined `#434451` borders instead of washed-out, fuzzy soft pastels.
3. **Zero Gradients**: Pure solid colors for sharp, professional presentation.
4. **High Contrast Typography**: `#25262E` guarantees effortless readability across all screens.
5. **Real Utility Icons**: Practical glyphs (`bi-pencil`, `bi-shield-check`, `bi-briefcase`, `bi-clock-history`).

---

## 📄 3. Template & Route Architecture

| Template File | Purpose | Route |
| :--- | :--- | :--- |
| [index.html](templates/index.html) | Dashboard & Core Workspace Tools | `/` |
| [login.html](templates/login.html) | User Authentication | `/login` |
| [signup.html](templates/signup.html) | User Registration | `/signup` |
| [resume_form.html](templates/resume_form.html) | Guided Resume Builder | `/resume/new` |
| [resume_detail.html](templates/resume_detail.html) | Profile Inspection & Export Hub | `/resume/<id>` |
| [resume_upload.html](templates/resume_upload.html) | ATS Scanner & Grammar Check | `/upload` |
| [compare.html](templates/compare.html) | Dual-Pane Job Description Matcher | `/compare` |
| [resume_improvement.html](templates/resume_improvement.html) | Experience Bullet Enhancer | `/improve` |
| [versions.html](templates/versions.html) | Saved Resumes & Versions History | `/versions` |
| [version_compare.html](templates/version_compare.html) | Side-by-Side Version Diff Engine | `/versions/compare` |
| [template_upload.html](templates/template_upload.html) | Custom DOCX / PDF Template Manager | `/templates/upload` |
| [job_description_upload.html](templates/job_description_upload.html) | Job Description Parser | `/upload_jd` |
| [ui.html](templates/ui.html) | Design System Showcase | `/ui` |
| [error.html](templates/error.html) | Friendly Error Page | Error handler |
