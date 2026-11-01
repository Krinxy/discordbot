class Voice:
    def __init__(self):
        self.lines = {
            "ticket_duplicate": "AHHH, I ALREADY HAVE THIS ONE. Status: **{status}**. Chill.",
            "ticket_reminder": "YOU SHALL NOT PASS! ...still. Check again:\n{content}\n{link}",
            "idle": "I'M HERE. Let's chill in this channel.",
            "music_queued": "FINE, IT'S IN THE QUEUE: {title}",
            "music_playing": "LET'S GOOO, NOW PLAYING: {title}",
            "music_unknown_command": "WHAT IS THAT SUPPOSED TO MEAN. Unknown command.",
            "troll_enabled": "TROLL MODE: ON. I'll show up uninvited sometimes.",
            "troll_disabled": "TROLL MODE: OFF. Back to being predictable.",
            "imdb_match": "GOT IT: **{title}** ({year}). Locked in.",
            "imdb_no_match": "COULDN'T FIND THAT ANYWHERE. Try a different title or paste the link.",
            "imdb_ambiguous_prompt": "FOUND A FEW OF THESE. PICK ONE:\n{options}",
            "imdb_pick_timeout": "NOBODY PICKED IN TIME. Forget it, post it again if you still want it.",
            "imdb_person_blacklisted": "NOPE. Not touching anything with that person in it.",
            "tickets_role_required": "YOU DON'T HAVE THE ROLE FOR THIS. Nice try.",
            "tickets_user_blacklisted": "YOU'RE BLOCKED FROM MAKING REQUESTS. Ask an operator.",
        }

    def get(self, key, **kwargs):
        return self.lines[key].format(**kwargs)
