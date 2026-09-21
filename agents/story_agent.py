#!/usr/bin/env python3
"""agents/story_agent.py — vinklar + hooks.
20 kandidatvinklar -> research-fit -> bästa konceptet (story.json).
"""
import os, json
from agents import llm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _title_variants(topic):
    return [
        f"The Story of {topic}",
        f"How {topic} Built an Empire Nobody Saw Coming",
        f"The Problem With {topic}",
        f"{topic}: Rise and Fall",
        f"What Really Happened to {topic}",
        f"The Dark Side of {topic}",
        f"{topic}, Explained in 8 Minutes",
        f"Inside the {topic} Machine",
        f"Why the Internet Turned on {topic}",
        f"The Untold Truth About {topic}",
        f"{topic}: The Moment Everything Changed",
        f"The Secret History of {topic}",
        f"How {topic} Broke the Internet",
        f"{topic} vs. Everyone",
        f"The Fall of {topic}",
        f"{topic}: Numbers That Don't Add Up",
        f"The Rise of {topic}",
        f"What {topic} Doesn't Want You to Know",
        f"{topic}: The Full Story",
        f"The Genius and the Problem With {topic}",
    ]

def run(topic, research, project_dir):
    facts = research["facts"]
    supports = lambda w: sum(1 for f in facts if w.lower() in f["claim"].lower())
    scored = sorted(((supports(t) + (0.5 if "problem" in t.lower() or "dark" in t.lower() else 0), t)
                     for t in _title_variants(topic)), reverse=True)
    chosen = scored[0][1]
    story = {
        "topic": topic,
        "hook": research["facts"][0]["claim"] if facts else topic,
        "angle": chosen,
        "angle_candidates": [t for _, t in scored[:10]],
        "why_now": f"Inga färska sökresultat krävdes häromkring ({len(facts)} claims)",
        "audience": "internet-dokumentär / true-story publik",
    }
    if llm.is_available():
        try:
            obj = llm.fill_json(
                f"Ge story-meta för en dokumentär om '{topic}' givet claims:\n"
                f"{json.dumps([f['claim'] for f in facts[:15]], ensure_ascii=False)}\n"
                f"Svara JSON: {{title, hook, angle, why_now, audience, curiosity_gap}}")
            if obj:
                story.update(obj)
        except Exception:
            pass
    os.makedirs(project_dir, exist_ok=True)
    with open(os.path.join(project_dir, "story.json"), "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=1)
    return story
