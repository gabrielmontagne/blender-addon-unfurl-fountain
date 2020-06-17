import bpy
from pathlib import Path

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
        print('xxxyttt!')
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
