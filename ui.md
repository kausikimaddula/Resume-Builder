# ResumeAI — UI Design System & Component Reference

This document provides a comprehensive guide and reference to the **ResumeAI** User Interface, built using **Tailwind CSS v4** and modern design principles.

---

## 🎨 1. Design Principles & Tokens

### Typography
* **Primary Font**: `Plus Jakarta Sans` (weights: `400` Regular, `500` Medium, `600` SemiBold, `700` Bold, `800` ExtraBold)
* **Fallback Fonts**: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`

### Color Palette

| Token Name | Hex Code | Tailwind Class | Usage |
| :--- | :--- | :--- | :--- |
| **Primary Blue** | `#2563eb` | `bg-blue-600` / `text-blue-600` | Primary actions, links, brand accents |
| **Primary Light** | `#eff6ff` | `bg-blue-50` / `text-blue-700` | Active nav items, icon backgrounds |
| **Accent Indigo** | `#4f46e5` | `bg-indigo-600` | Brand gradients, badges |
| **Success Emerald** | `#16a34a` | `bg-emerald-600` / `bg-emerald-50` | ATS pass scores, DB status, verified states |
| **Cyan / Teal** | `#0891b2` | `bg-cyan-600` / `bg-cyan-50` | Scanner cards, keyword highlights |
| **Warning Amber** | `#f59e0b` | `bg-amber-500` / `bg-amber-50` | Warnings, missing skill alerts |
| **Danger Rose** | `#e11d48` | `bg-rose-600` / `bg-rose-50` | Error messages, logout actions |
| **Neutral Dark** | `#0f172a` | `text-slate-900` / `bg-slate-900` | Headings, high-contrast text |
| **Neutral Muted** | `#64748b` | `text-slate-500` / `text-slate-600` | Subtext, captions, helper text |
| **Neutral Surface** | `#f8fafc` | `bg-slate-50` | Page background, cards, input backgrounds |
| **Neutral Border** | `#e2e8f0` | `border-slate-200` | Card borders, dividers, outlines |

---

## 🧩 2. Core Components

### 2.1 Navigation Bar (`base.html`)
Glassmorphism header with a sticky backdrop blur:
```html
<header class="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
  <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <!-- Logo -->
      <a class="flex items-center gap-2.5" href="/">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <i class="bi bi-file-earmark-person-fill text-lg"></i>
        </div>
        <span class="text-xl font-extrabold tracking-tight text-slate-900">
          Resume<span class="text-blue-600">AI</span>
        </span>
      </a>
      
      <!-- Nav Links -->
      <div class="hidden md:flex items-center gap-1">
        <a href="/" class="px-3.5 py-2 rounded-lg text-sm font-bold bg-blue-50 text-blue-700">Dashboard</a>
        <a href="/resume/new" class="px-3.5 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100">Build Resume</a>
        <a href="/upload" class="px-3.5 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100">ATS Scanner</a>
        <a href="/compare" class="px-3.5 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100">JD Matcher</a>
        <a href="/improve" class="px-3.5 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100">AI Improver</a>
        <a href="/versions" class="px-3.5 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100">Versions</a>
      </div>
    </div>
  </nav>
</header>
```

---

### 2.2 Action Buttons
```html
<!-- Primary Filled Button -->
<button class="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold text-sm shadow-md shadow-blue-500/20 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150">
  Primary Action &rarr;
</button>

<!-- Secondary Outline Button -->
<button class="px-6 py-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold text-sm shadow-xs hover:border-slate-300 hover:-translate-y-0.5 transition-all duration-150">
  Secondary Action
</button>

<!-- Soft Action Button -->
<button class="py-2.5 px-4 rounded-xl text-xs font-bold text-blue-600 bg-blue-50/80 hover:bg-blue-600 hover:text-white transition-all duration-150">
  Soft Action Button
</button>
```

---

### 2.3 Feature Tool Cards
Clean cards with subtle borders, glowing icon badges, and hover animations:
```html
<div class="group bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-xl hover:border-blue-300 hover:-translate-y-1 transition-all duration-200 flex flex-col">
  <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl mb-4 group-hover:scale-110 transition-transform duration-200">
    <i class="bi bi-pencil-square"></i>
  </div>
  <h3 class="text-base font-bold text-slate-900 mb-2">Resume Builder</h3>
  <p class="text-xs text-slate-500 leading-relaxed mb-6 flex-grow">
    Fill in our guided step-by-step form to build a structured, ATS-compliant resume.
  </p>
  <a href="/resume/new" class="inline-flex items-center justify-center gap-1.5 w-full py-2.5 px-4 rounded-xl text-xs font-bold text-blue-600 bg-blue-50/70 hover:bg-blue-600 hover:text-white transition-all duration-150">
    Start Building <i class="bi bi-arrow-right"></i>
  </a>
</div>
```

---

### 2.4 Form Inputs & Drag-and-Drop Dropzone
```html
<!-- Input with Icon -->
<div class="relative rounded-xl shadow-xs">
  <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 text-sm">
    <i class="bi bi-envelope"></i>
  </div>
  <input type="email" placeholder="name@example.com" class="block w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all">
</div>

<!-- Drag & Drop Dropzone -->
<div class="bg-white p-8 rounded-2xl border-2 border-dashed border-slate-300 hover:border-blue-500 hover:bg-blue-50/20 text-center transition-all cursor-pointer">
  <i class="bi bi-cloud-arrow-up text-4xl text-blue-600 mb-2 block"></i>
  <p class="text-sm font-bold text-slate-900 mb-1">Drag and drop your resume file here</p>
  <p class="text-xs text-slate-500 mb-3">or click to browse from your computer</p>
  <span class="inline-block px-3 py-1 bg-slate-100 rounded-full text-[11px] font-medium text-slate-600 border border-slate-200">
    Supports .docx, .pdf (Max: 5MB)
  </span>
</div>
```

---

## 📄 3. Template Architecture

| Template File | Purpose & Route |
| :--- | :--- |
| [`templates/base.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/base.html) | Global layout, Tailwind CSS v4 CDN, navbar, footer, and flash messages |
| [`templates/index.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/index.html) | Main Dashboard / Landing page (`/`) |
| [`templates/ui.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/ui.html) | Interactive UI Design System showcase (`/ui`) |
| [`templates/login.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/login.html) | User authentication & login (`/login`) |
| [`templates/signup.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/signup.html) | User account registration (`/signup`) |
| [`templates/resume_form.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/resume_form.html) | Step-by-step resume builder (`/resume/new`) |
| [`templates/resume_upload.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/resume_upload.html) | File parser & ATS score analyzer (`/upload`) |
| [`templates/compare.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/compare.html) | Job description keyword matcher (`/compare`) |
| [`templates/resume_improvement.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/resume_improvement.html) | AI bullet point enhancement (`/improve`) |
| [`templates/versions.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/templates/versions.html) | SQLite / PostgreSQL version history (`/versions`) |

---

## 🌐 4. Live UI Preview
* **App Home:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **UI Design System:** [http://127.0.0.1:5000/ui](http://127.0.0.1:5000/ui)
* **Standalone UI File:** Open [`ui.html`](file:///c:/Users/SAI%20KAUSIKI/OneDrive/Desktop/Resume-Builder/ui.html) directly in any browser.
