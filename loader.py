"""
A static resource-loading class with automatic caching of images and audio effects.
"""

import pygame


class Loader:
    images = {}
    audio = {}
    image_dir = 'images'
    audio_dir = 'audio'

    @classmethod
    def clear(cls, key=None):
        """
        Remove cached resource with the given key or clear all resources if no key is specified.

        :param key: File to remove, e.g. "Song.wav" or "Image.png --scale 2 --rotate 90 mirror"
        """

        if key:
            if key in cls.images:
                del cls.images[key]
            if key in cls.audio:
                del cls.audio[key]
        else:
            cls.images = {}
            cls.audio = {}

    @classmethod
    def animation(cls, filename, frames=1, alpha=False, colorkey=-1, scale=1, mirror=False, rotate=0):
        """
        Load an animation from a sprite-sheet, adding it to the cache if not previously loaded.

        :param filename: Filename of the sprite-sheet (defaults to PNG if no extension is included)
        :param frames: Number of frames in the animation
        :param alpha: Load the image with per-pixel alpha values (overrides colorkey)
        :param colorkey: Apply this RGB tuple colorkey to the transparent pixels in the image (defaults to color of
                         top-left pixel), set to None to disable
        :param scale: The image will be scaled by this factor (e.g. scale=2 will double the size)
        :param mirror: The image will be horizontally flipped if this parameter is True
        :param rotate: The image will be rotated counterclockwise by this angle in degrees (after any mirroring)
        :returns: A list of pygame Surfaces containing the animation frames
        """

        if '.' not in filename:
            filename = f'{filename}.png'
        key = filename
        if scale:
            key = f'{key} --scale {scale}'
        if mirror:
            key = f'{key} --mirror'
        if rotate:
            key = f'{key} --rotate {rotate}'
        if key in cls.images:
            return cls.images[key]
        sheet = pygame.image.load(f'{cls.image_dir}/{filename}')
        if scale != 1:
            sheet = pygame.transform.scale(sheet, [scale * sheet.get_width(), scale * sheet.get_height()])
        if frames == 1:
            animation = [sheet]
        else:
            w = sheet.get_width() / frames
            h = sheet.get_height()
            animation = []
            for i in range(frames):
                animation.append(sheet.subsurface((w * i, 0, w, h)))
        for i in range(frames):
            if alpha:
                animation[i] = animation[i].convert_alpha()
            elif colorkey:
                ck = sheet.get_at((0, 0)) if colorkey == -1 else colorkey
                surface = pygame.Surface(animation[i].get_size())
                surface.fill(ck)
                surface.blit(animation[i], (0, 0))
                surface.set_colorkey(ck)
                animation[i] = surface.convert()
            else:
                animation[i] = animation[i].convert()
            if mirror:
                animation[i] = pygame.transform.flip(animation[i], mirror, False)
            if rotate:
                animation[i] = pygame.transform.rotate(animation[i], rotate)
        cls.images[key] = animation
        return animation

    @classmethod
    def image(cls, filename, alpha=False, colorkey=-1, scale=1, mirror=False, rotate=0):
        """
        Load an animation from a sprite-sheet, adding it to the cache if not previously loaded.

        :param filename: Filename of the sprite-sheet (defaults to PNG if no extension is included)
        :param alpha: Load the image with per-pixel alpha values (overrides colorkey)
        :param colorkey: Apply this RGB tuple colorkey to the transparent pixels in the image (defaults to color of
                         top-left pixel), set to None to disable
        :param scale: The image will be scaled by this factor (e.g. scale=2 will double the size)
        :param mirror: The image will be horizontally flipped if this parameter is True
        :param rotate: The image will be rotated counterclockwise by this angle in degrees (after any mirroring)
        :returns: A pygame Surface containing the image
        """

        return cls.animation(filename, frames=1, alpha=alpha, colorkey=colorkey, scale=scale, mirror=mirror,
                             rotate=rotate)[0]

    @classmethod
    def sound(cls, filename, volume=1):
        """
        Plays the given sound effect, adding it to the cache if not previously loaded

        :param filename: Filename of the audio file (defaults to WAV if no extension is included)
        :param volume: Scale the volume of the sound effect (set to zero to stop the sound effect early)
        :return: The loaded pygame.Sound object
        """

        if '.' not in filename:
            filename = f'{filename}.wav'
        if filename in cls.audio:
            sound = cls.audio[filename]
        else:
            sound = pygame.mixer.Sound(f'{cls.audio_dir}/{filename}')
            cls.audio[filename] = sound
        if volume:
            sound.set_volume(volume)
        return sound

    @classmethod
    def music(cls, filename):
        """
        Plays the given background track (without caching). For more advanced functionality call pygame.mixer.music
        methods directly.

        :param filename: Filename of the audio file (defaults to WAV if no extension is included)
        :return: pygame.mixer.music (for consistency with the other Loader methods)
        """

        pygame.mixer.music.load(f'{cls.audio_dir}/{filename}')
        return pygame.mixer.music
