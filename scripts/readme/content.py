"""Everything the README images say. Edit here, then run build.py."""

PROFILE = {
    "name": "Kwik Andreas",
    "alt": "Kwik Andreas. I build full-stack web apps and 3D games, and I care about making both feel fast. "
           "Available for work. Informatics at Universitas Bunda Mulia, Jakarta. Top 2% at the BI DIGDAYA X Hackathon 2026.",
    "where": "Jakarta, ID · GMT+7",
    "strip": ["Available for work", "Informatics @ UBM", "Top 2% · BI DIGDAYA X 2026", "Scroll ↓"],
    "year": 2026,
}

# Newest first, same order as the portfolio (src/content/projects.ts).
# `hint` is what the card says it opens; the README links the card to the same place.
PROJECTS = [
    dict(slug="myagentmd", title="My Agent MD", shot="myagentmd.webp", categories=["Web", "AI"],
         summary="Generator for AGENTS.md configuration files tailored to a project's requirements.",
         stack=["Next.js", "Tailwind CSS"], hint="Live", url="https://myagentmd.vercel.app/",
         repo="https://github.com/KwikAndreas/myagentmd"),
    dict(slug="revdadas", title="Revenue Daerah Cerdas", shot="revdadas.webp", categories=["Web", "AI"],
         summary="Forecasting platform that projects potential local tax and levy revenue with precomputed ML models.",
         stack=["Python", "Prophet", "Next.js", "Tailwind CSS"], hint="Live", url="https://revdadas.vercel.app/",
         repo="https://github.com/KwikAndreas/revdadas"),
    dict(slug="legacybot", title="Legacy Bot", shot="legacybot.webp", categories=["AI"],
         summary="Chatbot that uses reinforcement learning to adapt from its previous responses.",
         stack=["Python", "Reinforcement Learning", "NLP"], hint="Repo", url="https://github.com/KwikAndreas/legacybot",
         repo="https://github.com/KwikAndreas/legacybot"),
    dict(slug="gkicinda", title="GKI Cipinang Indah", shot="gkicinda.webp", categories=["Web"],
         summary="Church website with member data, service schedules and activity announcements.",
         stack=["Vite", "TypeScript", "Tailwind CSS", "Supabase"], hint="Live", url="https://gkicinda.id",
         repo=None),
    dict(slug="pingx", title="PingX", shot="pingx.webp", categories=["Tools"],
         summary="npm CLI package for monitoring server latency and network connections in the terminal.",
         stack=["Node.js", "TypeScript", "CLI"], hint="npm", url="https://www.npmjs.com/package/@xavorus/pingx",
         repo="https://github.com/KwikAndreas/pingx"),
    dict(slug="kelasbios", title="KelasBIOS", shot="kelasbios.webp", categories=["Web"],
         summary="Registration platform for HIMA BIOS members and class sessions, with a full admin dashboard.",
         stack=["Next.js", "Tailwind CSS", "Supabase", "SQL"], hint="Live", url="https://kelasbios.vercel.app/",
         repo="https://github.com/KwikAndreas/kelasbios"),
    dict(slug="himabios", title="HIMA BIOS Website", shot="himabios.webp", categories=["Web"],
         summary="Official site of the Informatics Student Association: history, structure and news.",
         stack=["Next.js", "TypeScript", "Tailwind CSS", "MDX"], hint="Live", url="https://himabios.vercel.app/",
         repo="https://github.com/KwikAndreas/himabios"),
    dict(slug="carrush", title="Car Rush", shot="carrush.webp", categories=["Game"],
         summary="Mobile endless runner built with Unity, with 3D assets modelled in Blender.",
         stack=["Unity 6", "C#", "Blender"], hint="Play", url="https://bit-grow.itch.io/carrush",
         repo=None),
]

ABOUT = {
    "bio": "Informatics student in Jakarta. I build full-stack web apps with Next.js and interactive "
           "3D games with Unity and C#, and I care about making both feel fast.",
    "edu_title": "Informatics",
    "edu_school": "Universitas Bunda Mulia",
    "stack": [
        ("Web", ["Next.js", "React", "TypeScript", "Tailwind CSS"]),
        ("Backend & data", ["Node.js", "Python", "Supabase"]),
        ("Game & 3D", ["Unity", "C#", "Blender"]),
    ],
}

MILESTONES = {
    "highlight": dict(year=2026, big="Top 2%", sub="43 of 2,800 teams",
                      title="Top 2% Team Finalist", issuer="Bank Indonesia DIGDAYA X Hackathon",
                      body="Team finalist at the Bank Indonesia DIGDAYA X Hackathon 2026."),
    "timeline": [
        dict(year=2026, title="Fundamental Deep Learning", issuer="DIGDAYA Bank Indonesia × Dicoding"),
        dict(year=2026, title="UX Design", issuer="DIGDAYA Bank Indonesia × Dicoding"),
        dict(year=2025, title="3rd Place, AI-Based Game Design", issuer="Universitas Bunda Mulia"),
        dict(year=2024, title="Samsung Innovation Campus", issuer="Completed Stage 1 · Advanced Python & Data Structures (Gold)"),
        dict(year=2024, title="Linux System Administration", issuer="Boer Technology"),
        dict(year=2023, title="KKNI Level 2, Multimedia", issuer="LSP / BNSP"),
    ],
}

CONTACT = {"email": "kwikandreasjonathan@gmail.com"}

# Starting values for dark_mode.svg / light_mode.svg. today.py overwrites them daily.
STATS_SEED = dict(repo="61", contrib="68", commit="757", star="14", follower="9",
                  loc="4,851,031", loc_add="10,707,778", loc_del="5,856,747")
