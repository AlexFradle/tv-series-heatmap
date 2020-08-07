import pygame
import os
from imdb import IMDb
from colour import Color
import requests
import io
from PIL import Image
pygame.init()


class HeatMap(pygame.Surface):
    def __init__(self, w, h, f):
        super().__init__((w, h))
        self.w, self.h = w, h
        self.font = f
        self.search = False
        self.cover_img = None
        self.overall_rating = None
        self.title = None

    def update(self, text):
        if self.search:
            self.fill((255, 255, 255))
            im = IMDb()
            series = im.search_movie(text)[0]

            # Get title
            self.title = series["long imdb title"]

            # Get cover image
            cover = series["full-size cover url"]
            r = requests.get(cover)
            img = Image.open(io.BytesIO(r.content))
            img = img.resize((256, 384))

            self.cover_img = pygame.image.fromstring(img.tobytes(), img.size, img.mode)

            self.overall_rating = im.get_movie(series.getID())["rating"]

            if series["kind"] == "tv series":
                im.update(series, "episodes")
                num_of_series = sorted(series["episodes"].keys())

                ratings = []

                # Get each episodes rating
                for s in num_of_series:
                    num_of_episodes = sorted(series["episodes"][s].keys())
                    e_ratings = []
                    for e in num_of_episodes:
                        e_ratings.append(series["episodes"][s][e].get("rating", 0))
                    ratings.append(e_ratings)

                # Get box sizes
                max_episodes = max(ratings, key=len)
                box_width = (self.w - 30) / len(max_episodes)
                box_height = (self.h - 30) / len(ratings)

                # Draw axis labels
                self.blit(self.font.render("Episodes", True, (0, 0, 0)), ((self.w // 2) - (font.size("Episodes")[0] // 2), 0))

                letter_size = font.size("S")
                vert_start = (self.h // 2) - ((letter_size[1] * 6) // 2)
                for pos, letter in enumerate("Series"):
                    self.blit(self.font.render(letter, True, (0, 0, 0)), (0, vert_start + (letter_size[1] * pos)))

                # Get colour gradient
                colours = list(Color("red").range_to(Color("green"), 50))
                colours[:0] = [Color("red")] * 50

                # Insert blank episode spaces
                for s in ratings:
                    if len(s) < len(max_episodes):
                        s.extend([None] * (len(max_episodes) - len(s)))

                # Draw episode text
                for en in range(len(max_episodes)):
                    e_txt = self.font.render(str(en + 1), True, (0, 0, 0))
                    et_pos = ((en * box_width) + 30 + (box_width // 2), 15)
                    self.blit(e_txt, et_pos)

                # Series loop
                for s_pos, s in enumerate(ratings):
                    # Draw series text
                    s_txt = self.font.render(str(s_pos + 1), True, (0, 0, 0))
                    st_pos = (15, (s_pos * box_height) + 30 + (box_height // 2))
                    self.blit(s_txt, st_pos)
                    # Episode loop
                    for e_pos, e in enumerate(s):
                        e_rect = pygame.Rect((e_pos * box_width) + 30, (s_pos * box_height) + 30, box_width, box_height)
                        if e is not None:
                            # Draw episode rect
                            c = list(map(lambda x: x * 255, colours[int(e * 10) - (1 if e > 0 else 0)].rgb))
                            pygame.draw.rect(self, c, e_rect)

                            # Draw rating text
                            r_txt = self.font.render(str(e)[:3], True, (0, 0, 0))
                            r_size = font.size(str(e)[:3])
                            r_pos = (e_rect.centerx - (r_size[0] // 2), e_rect.centery - (r_size[1] // 2))
                            self.blit(r_txt, r_pos)

                        pygame.draw.rect(self, (0, 0, 0), e_rect, 2)
            else:
                self.blit(font.render("NOT A SERIES", True, (0, 0, 0)), (self.w // 2, self.h // 2))

        self.search = False


class SearchLine(pygame.Surface):
    def __init__(self, w, h, f):
        super().__init__((w, h))
        self.w, self.h = w, h
        self.text = ""
        self.font = f

    def update(self, keys):
        self.fill((0, 0, 0))
        self.text += "".join(keys)
        txt = self.font.render(self.text, True, (255, 255, 255))
        size = font.size(self.text)
        pos = ((self.w // 2) - (size[0] // 2), (self.h // 2) - (size[1] // 2))
        self.blit(txt, pos)

    def remove_chr(self):
        self.text = self.text[:-1]


os.environ["SDL_VIDEO_CENTERED"] = "1"
width, height = 1280, 720

display = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.font.SysFont("courier", 15, True)

sl = SearchLine(width // 3, height // 12, font)
hm = HeatMap(width // 1.25, height // 1.1, font)

pressed = []

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_BACKSPACE:
                sl.remove_chr()
                sl.update(pressed)
            elif event.key == pygame.K_RETURN:
                hm.search = True
            else:
                pressed.append(chr(event.key))
                sl.update(pressed)

    display.fill((255, 255, 255))

    hm.update(sl.text)

    display.blit(sl, (width // 3, height - sl.h))
    display.blit(hm, (0, 0))

    # Draw series cover image
    if hm.cover_img is not None:
        display.blit(hm.cover_img, (hm.w, 30))

    # Draw series title text
    if hm.title is not None:
        ts = font.size(hm.title)
        display.blit(font.render(hm.title, True, (0, 0, 0)), ((hm.w + ((width - hm.w) // 2)) - (ts[0] // 2), 430))

    # Draw rating text
    if hm.overall_rating is not None:
        rs = font.size("Rating: " + str(hm.overall_rating))
        display.blit(font.render("Rating: " + str(hm.overall_rating), True, (0, 0, 0)), ((hm.w + ((width - hm.w) // 2)) - (rs[0] // 2), 450))

    pressed = []
    pygame.display.update()
    clock.tick(60)

pygame.quit()

