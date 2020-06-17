from pathlib import Path
import bpy
import os
import sys
import re

internal_blend = re.compile('\w+\.blend')
current_dir = os.path.dirname(internal_blend.split(__file__)[0])
sys.path.append(current_dir)

from fountain import Fountain

spaces = re.compile(r'\s+')
words_per_second = 0.7
line_break_seconds = 0.4

def text_to_seconds(text):
    words = len(spaces.split(text))
    return words_per_second * words + line_break_seconds * text.count('\n')

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
        
        fountain_script = bpy.context.area.spaces.active.text.as_string()
        if fountain_script.strip() == "": return {"CANCELLED"}
        F = Fountain(fountain_script)

        render = context.scene.render
        fps = round((render.fps / render.fps_base), 3)

        for fc, f in enumerate(F.elements):
            if f.element_type != 'Dialogue': continue
            text = f.element_text.strip()
            print(text, round(text_to_seconds(text), 3))

        print('fps', fps)

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

classes = (UNFURL_FOUNTAIN_PT_panel, UNFURL_FOUNTAIN_OT_to_strips)

def register():
    from bpy.utils import register_class

    print('registering')

    for cls in classes :
        register_class(cls)

def unregister():
    print('un-registering')


if __name__ == '__main__':
    register()
