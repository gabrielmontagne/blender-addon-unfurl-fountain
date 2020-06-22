"""Based on code by tin2tin, https://github.com/tin2tin/Blender_Screenwriter"""

from collections import namedtuple
from math import ceil
from pathlib import Path
import bpy
import os
import re
import sys


bl_info = {
    'name': 'Unfurn Fountain to VSE text strips',
    'author': 'gabriel montagné, gabriel@tibas.london',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    'description': 'Unfurl fountain scripts to VSE text strips',
    'tracker_url': 'https://github.com/gabrielmontagne/blender-addon-unfurl-fountain/issues'
}

internal_blend = re.compile('\w+\.blend')
current_dir = os.path.dirname(internal_blend.split(__file__)[0])
sys.path.append(current_dir)

from fountain import Fountain

spaces = re.compile(r'\s+')
words_per_second = 3.75
text_speed_factor = 1.2
min_text_length = 1.5
line_break_seconds = 0.3
scene_padding_seconds = 1

Scene = namedtuple('Scene', ['name', 'elements'])
Dialogue = namedtuple('Dialogue', ['seconds', 'character', 'parenthetical', 'text'])
Action = namedtuple('Action', ['seconds', 'text'])

def text_to_seconds(text):
    words = len(spaces.split(text))
    return max(min_text_length, round(words / words_per_second + line_break_seconds * text.count('\n'), 2))

def find_empty_channel():
    context = bpy.context

    if not context.scene.sequence_editor:
        context.scene.sequence_editor_create()

    sequences = context.sequences
    if not sequences:
        return 1

    channels = [s.channel for s in sequences]
    channels = sorted(list(set(channels)))
    return channels[-1] + 1

def seconds_to_frames(seconds):
    render = bpy.context.scene.render
    return ceil((render.fps / render.fps_base) * seconds)

def to_scenes(script):
    F = Fountain(script)
    scenes = []

    current_scene = None
    current_char = None
    current_parenthetical = ''

    for fc, f in enumerate(F.elements):
        element_type = f.element_type
        text = f.element_text.strip()

        if element_type == 'Scene Heading':
            name = f.original_content.strip()
            current_scene = Scene(name, [])
            scenes.append(current_scene)

        elif not current_scene:
            continue

        elif element_type == 'Parenthetical':
            current_parenthetical = text

        elif element_type == 'Character':
            current_char = text

        elif element_type == 'Dialogue':
            seconds = text_to_seconds(text) * text_speed_factor
            current_scene.elements.append(
                Dialogue(
                seconds,
                current_char,
                current_parenthetical,
                text
            ))
            current_parenthetical = ''

        elif current_scene and element_type == 'Action':
            seconds = text_to_seconds(text)
            current_scene.elements.append(Action(seconds, text))

    return scenes

def lay_out_scenes(scenes):
    next = 0
    channel = find_empty_channel()

    for i, s in enumerate(scenes):
        total = scene_padding_seconds

        for e in s.elements:
            start = total
            end = total + e.seconds

            element_type = type(e)
            if element_type is Dialogue:
                strip = create_strip(
                    channel + 1,
                    start + next,
                    end + next,
                    '{}{}: {}'.format(e.character, (
                        e.parenthetical and ' ' + e.parenthetical),
                        e.text)
                )

                strip.location.y = 0.1
                strip.align_y = 'BOTTOM'

            elif element_type is Action:
                strip = create_strip(channel + 2, start + next, end + next, e.text)
                strip.location.y = 0.5
                strip.align_y = 'CENTER'

            total = end

        total += scene_padding_seconds
        end = next + total

        strip = create_strip(channel, next, next + total, s.name)
        strip.location.y = 0.9
        strip.align_y = 'TOP'
        next = end

def create_strip(channel, start, end, text):
    frame_start = seconds_to_frames(start)
    frame_end = seconds_to_frames(end)

    strip = bpy.context.scene.sequence_editor.sequences.new_effect(
        name=text,
        type='TEXT',
        channel=channel,
        frame_start=frame_start,
        frame_end=frame_end
    )

    strip.font_size = int(bpy.context.scene.render.resolution_y/18)
    strip.use_shadow = True
    strip.select= True
    strip.wrap_width = 0.85
    strip.text = text
    strip.blend_type = 'ALPHA_OVER'
    return strip

class UNFURL_FOUNTAIN_OT_strips_to_markers(bpy.types.Operator):
    '''Mark timeline from strips'''
    bl_idname = "unfurl.strips_to_markers"
    bl_label = "Mark timeline from strips"

    def execute(self, context):
        selected_frames = {s.frame_start for s in context.selected_sequences}
        timeline_markers = context.scene.timeline_markers
        for frame in selected_frames:
            timeline_markers.new(name='F_{}'.format(frame), frame=frame)

        return {'FINISHED'}
    
class UNFURL_FOUNTAIN_OT_clear_markers(bpy.types.Operator):
    '''Mark timeline from strips'''
    bl_idname = "unfurl.clear_markers"
    bl_label = "Clear timeline markers"

    def execute(self, context):
        context.scene.timeline_markers.clear()
        return { 'FINISHED' }


class UNFURL_FOUNTAIN_OT_to_strips(bpy.types.Operator):
    '''Unfurl foutain to text strips'''
    bl_idname = "unfurl.fountain_to_strips"
    bl_label = "Unfurl foutain to strips"

    @classmethod
    def poll(cls, context):
        space = bpy.context.space_data
        try:
            filepath = space.text.name
            if filepath.strip() == "": return False
            return ((space.type == 'TEXT_EDITOR')
                    and Path(filepath).suffix == ".fountain")
        except AttributeError: return False

    def execute(self, context):

        script = bpy.context.area.spaces.active.text.as_string()
        if script.strip() == "": return {"CANCELLED"}

        scenes = to_scenes(script)
        lay_out_scenes(scenes)

        return {"FINISHED"}

class UNFURL_FOUNTAIN_PT_panel(bpy.types.Panel):
    """Unfurl fountain controls"""
    bl_label = "Unfurl fountain"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Text"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("unfurl.fountain_to_strips")
        row = layout.row(align=True)
        row.operator("unfurl.strips_to_markers")
        row = layout.row(align=True)
        row.operator("unfurl.clear_markers")

classes = (UNFURL_FOUNTAIN_PT_panel, UNFURL_FOUNTAIN_OT_to_strips, UNFURL_FOUNTAIN_OT_strips_to_markers, UNFURL_FOUNTAIN_OT_clear_markers)

def register():
    from bpy.utils import register_class
    for cls in classes :
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes :
        unregister_class(cls)

if __name__ == '__main__':
    register()
