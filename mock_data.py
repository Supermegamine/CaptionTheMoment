"""Static mock data for the Caption The Moment demo.

Edit this file to change the demo content. To use real photos instead of the
illustrated scenes, drop them into ``demo_assets/`` and point ``file`` at them
(and add them as <app-file> entries in index.html so the browser build ships them).
"""

ROOM_ID = "demo01-0000-0000-0000-000000000000"
ROOM_TITLE = "Friday Night Photo Roast"

# One entry per image. ``captions`` are (player name, caption text), oldest first.
IMAGES = [
    {
        "id": "img-katze",
        "file": "demo_assets/katze.png",
        "filename": "katze.png",
        "captions": [
            ("Mia", "Das war nicht die Gurke. Das war ein Angriff auf meine Würde."),
            ("Jonas", "Wer hat eine Schlange in die Küche gelassen?!"),
            ("Lena", "Ich hab sie 14 Minuten angestarrt. Sie hat sich bewegt. Ich schwöre."),
            ("Tim", "Mein Therapeut sagt, ich soll mich meinen Ängsten stellen. Er hat diese Gurke nicht gesehen."),
        ],
    },
    {
        "id": "img-hund",
        "file": "demo_assets/hund.png",
        "filename": "hund.png",
        "captions": [
            ("Sarah", "Hätte eine E-Mail sein können. Ich hab 'Allen antworten' gedrückt."),
            ("Max", "Ich habe keine Ahnung, was ich tue. Aber ich tue es mit Sonnenbrille."),
            ("Nora", "Gehalt: Leckerlis. Titel: Senior Good Boy."),
            ("Felix", "Ich bin nicht im Homeoffice. Das Homeoffice ist in mir."),
        ],
    },
    {
        "id": "img-pinguine",
        "file": "demo_assets/pinguine.png",
        "filename": "pinguine.png",
        "captions": [
            ("Mia", "Jedes Gruppenfoto: Vier lächeln, einer hat 'Kevin' auf dem Namensschild."),
            ("Lena", "Kevin hat 'Bitte alle nach vorne schauen' als persönliche Beleidigung verstanden."),
            ("Tim", "Er hat gehört, hinten gibt's Fisch."),
            ("Max", "Kevin, wenn du noch einmal 'Ich bin halt Individualist' sagst, schubse ich dich vom Eisberg."),
        ],
    },
    {
        "id": "img-moewe",
        "file": "demo_assets/moewe.png",
        "filename": "moewe.png",
        "captions": [
            ("Nora", "Das ist kein Diebstahl. Das ist Pommes-Umverteilung."),
            ("Felix", "Ich hab sie mir verdient. Durch Schreien."),
            ("Sarah", "Ich bin nicht wegen dem Brot hier. Ich bin wegen Kohlenhydraten mit Ketchup hier."),
            ("Max", "'Du isst die nicht mehr, oder?' – hat er gefragt, nachdem er sie schon hatte."),
        ],
    },
]
