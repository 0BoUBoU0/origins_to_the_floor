bl_info = {
    "name": "Origins on the floor",
    "author": "Yannick 'BoUBoU' Castaing",
    "description": "this simple tool will move the origin of each selected meshes to its lower part",
    "location": "View3D > Object > Set Origin",
    "doc_url": "",
    "warning": "",
    "category": "Object",
    "blender": (2,90,0),
    "version": (1,3,6)
}

# get addon name and version to use them automaticaly in the addon
Addon_Name = str(bl_info["name"])
Addon_Version = str(bl_info["version"])
Addon_Version = Addon_Version[1:-1].replace(",",".")

# import modules
import bpy

# define global variables
debug_mode = False
separator = "-" * 20

## preferences
class OOTF_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    still_origin_override : bpy.props.BoolProperty (name="",description="will override the operator behavior",default=False)
    still_origin : bpy.props.BoolProperty (name="",description="By default behavior about the orgin. True means the mesh will move, False means the origin will move",default=True)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.active = self.still_origin_override
        box.label(text="Still Origin override")
        row = box.row()
        row.prop(self, "still_origin_override")
        row.label(text="Still origin: ")
        row.prop(self, "still_origin") 

# define menu
def originFloor_menu_draw(self,context):
    self.layout.operator('object.origins_on_the_floor',text="Origin to Floor", icon="SORT_ASC")
    # self.layout.operator('object.origins_on_the_left',icon="SORT_ASC")
    # self.layout.operator('object.origins_on_the_right',icon="SORT_ASC")
    # self.layout.operator('object.origins_on_the_top',icon="SORT_DESC")

def getverticeslist(object,smoothed):
    sel_obj = object
#            print(f"obj : {sel_obj}")
    object_copy = ""
    # if user want a smoothed version : copy
    if smoothed == True:
        object_copy = bpy.data.objects[sel_obj].copy()
        object_copy.name = f"{sel_obj}_copytemp"
        bpy.context.scene.collection.objects.link(bpy.data.objects[object_copy.name])
        if len(bpy.data.objects[sel_obj].modifiers) != 0 and "Subdivision" in bpy.data.objects[sel_obj].modifiers[-1].name:
            modifier_name = bpy.data.objects[sel_obj].modifiers[bpy.data.objects[sel_obj].modifiers[-1].name].name       
        else:
            modifier_name = "Subdivision_tempOrigin"
            bpy.data.objects[object_copy.name].modifiers.new(modifier_name, 'SUBSURF')
            bpy.data.objects[object_copy.name].modifiers[modifier_name].levels = 2
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[object_copy.name]
        bpy.context.object.data = bpy.context.object.data.copy()
#                print(object_copy.name)
#                print(modifier_name)
        bpy.ops.object.modifier_apply(modifier=modifier_name)
        obj_origin = bpy.data.objects[object_copy.name]
    else:
        obj_origin = bpy.data.objects[sel_obj]
    bpy.ops.object.select_all(action='DESELECT')
    obj_origin.select_set(True)    
    bpy.context.view_layer.objects.active = obj_origin
    # if user want centered on x and y
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # get vertex coordinates list (multiplied by the object matrix to get it in world space)
    vert_coord_list = []
    for vertex in obj_origin.data.vertices:
        transformed_vert = obj_origin.matrix_world @ vertex.co
        vert_coord_list.append(transformed_vert)
    flat_vert_coord_list = []
    # fatten vector list
    for sublist in vert_coord_list:
        for item in sublist:
            flat_vert_coord_list.append(item)
    return [flat_vert_coord_list,object_copy]
    

# create operator UPPER_OT_lower and idname = upper.lower         
class OBJECT_OT_ootf(bpy.types.Operator):
    bl_idname = 'object.origins_on_the_floor'
    bl_label = f"{Addon_Name} - {Addon_Version}"
    bl_description = "Move the origin at the lower part of your selected meshes"
    bl_options = {"REGISTER", "UNDO"}
    
    # redo panel = user interraction
    
    still_origin: bpy.props.BoolProperty(
            name = "Still Origin",
            description = "The origin will be still, only the mesh will move",
            default=False,
    ) 
    
    origins_XY_smoothed: bpy.props.BoolProperty(
            name = "Origins on smoothed mesh",
            description = "Will get the floor of the soothed version of each selected objects (/!\ slower process /!\)",
            default=False,
    ) 
    origins_options = [("Centered","Centered","Centered",0),("Floor","Floor","Floor",1),("Ceil","Ceil","Ceil",2),("Still","Still","Still",3)]
    origins_axisX_prop : bpy.props.EnumProperty(name = "X axis behavior",description = "How the axis behave",items = origins_options,default=0)
    origins_axisY_prop : bpy.props.EnumProperty(name = "Y axis behavior",description = "How the axis behave",items = origins_options,default=0)
    origins_axisZ_prop : bpy.props.EnumProperty(name = "Z axis behavior",description = "How the axis behave",items = origins_options,default=1)
    
      
    def execute(self, context):
        print(f"\n {separator} Begin {Addon_Name} {separator} \n")
        
        # store cursor transforms
        orig_cursor_loc = bpy.context.scene.cursor.location
        orig_cursor_rot = bpy.context.scene.cursor.rotation_euler

        # on 0 to avoid mistakes
        bpy.context.scene.cursor.location = (0,0,0)
        bpy.context.scene.cursor.rotation_euler = (0,0,0)
        
        # save selection set
        selected_obj = []
        for obj in bpy.context.selected_objects:
            selected_obj.append(obj.name)
        
        # make pivot for all objects in selection   
        for sel_obj in selected_obj:
            obj_locations_x = bpy.data.objects[sel_obj].location.x
            obj_locations_y = bpy.data.objects[sel_obj].location.y
            obj_locations_z = bpy.data.objects[sel_obj].location.z
#            print(f"obj : {sel_obj}")

            flat_vert_coord_list = getverticeslist(sel_obj,self.origins_XY_smoothed)

            # if user want a smoothed version : copy
            if self.origins_XY_smoothed == True:
                object_copy = bpy.data.objects[sel_obj].copy()
                object_copy.name = f"{sel_obj}_copytemp"
                bpy.context.scene.collection.objects.link(bpy.data.objects[object_copy.name])
                if len(bpy.data.objects[sel_obj].modifiers) != 0 and "Subdivision" in bpy.data.objects[sel_obj].modifiers[-1].name:
                    modifier_name = bpy.data.objects[sel_obj].modifiers[bpy.data.objects[sel_obj].modifiers[-1].name].name       
                else:
                    modifier_name = "Subdivision_tempOrigin"
                    bpy.data.objects[object_copy.name].modifiers.new(modifier_name, 'SUBSURF')
                    bpy.data.objects[object_copy.name].modifiers[modifier_name].levels = 2
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[object_copy.name]
                bpy.context.object.data = bpy.context.object.data.copy()
#                print(object_copy.name)
#                print(modifier_name)
                bpy.ops.object.modifier_apply(modifier=modifier_name)
                obj_origin = bpy.data.objects[object_copy.name]
            else:
                obj_origin = bpy.data.objects[sel_obj]
            bpy.ops.object.select_all(action='DESELECT')
            obj_origin.select_set(True)    
            bpy.context.view_layer.objects.active = obj_origin
            # if user want centered on x and y
            #if self.origins_XY_centered == True:
            #    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            # get vertex coordinates list (multiplied by the object matrix to get it in world space)
            vert_coord_list = []
            for vertex in obj_origin.data.vertices:
                transformed_vert = obj_origin.matrix_world @ vertex.co
                vert_coord_list.append(transformed_vert)    
            #print(f"{vert_coord_list=}")
            flat_vert_coord_list = []
            # fatten vector list
            for sublist in vert_coord_list:
                for item in sublist:
                    flat_vert_coord_list.append(item)
            #print(f"{flat_vert_coord_list=}")

            # get only the lowest X coordinates
            vert_x_list = flat_vert_coord_list[0::3]
            vert_x_list = sorted(vert_x_list)
            x_lowest_value = vert_x_list[0] 
            # get only the lowest Y coordinates
            vert_y_list = flat_vert_coord_list[1::3]
            vert_y_list = sorted(vert_y_list)
            y_lowest_value = vert_y_list[0] 
            # get only the lowest Z coordinates
            vert_z_list = flat_vert_coord_list[2::3]
            vert_z_list = sorted(vert_z_list)
            z_lowest_value = vert_z_list[0] 
            
            # print(f"{vert_x_list=}")
            # print(f"{vert_y_list=}")
            # print(f"{vert_z_list=}")
            
            # get locations
            loc_x = bpy.data.objects[obj_origin.name].location.x
            loc_y = bpy.data.objects[obj_origin.name].location.y
            loc_z = bpy.data.objects[obj_origin.name].location.z
            # use cursor to apply the pivot location
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[sel_obj].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[sel_obj]
#            print(f"{loc_x} ; {loc_y} ; {z_lowest_value}")
            ## get user preferences on X
            if self.origins_axisX_prop == "Centered":
                pos_x = loc_x
            elif self.origins_axisX_prop == "Floor":
                pos_x = vert_x_list[0]
            elif self.origins_axisX_prop == "Ceil":
                pos_x = vert_x_list[-1]    
            elif self.origins_axisX_prop == "Still":
                pos_x = obj_locations_x
            ## get user preferences on Y
            if self.origins_axisY_prop == "Centered":
                pos_y = loc_y
            elif self.origins_axisY_prop == "Floor":
                pos_y = vert_y_list[0]
            elif self.origins_axisY_prop == "Ceil":
                pos_y = vert_y_list[-1]   
            elif self.origins_axisY_prop == "Still":
                pos_y = obj_locations_y    
            ## get user preferences on Z
            if self.origins_axisZ_prop == "Centered":
                pos_z = loc_z
            elif self.origins_axisZ_prop == "Floor":
                pos_z = vert_z_list[0]
            elif self.origins_axisZ_prop == "Ceil":
                pos_z = vert_z_list[-1]   
            elif self.origins_axisZ_prop == "Still":
                pos_z = obj_locations_z
            bpy.context.scene.cursor.location = (pos_x,pos_y,pos_z)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            # delete smooth object if true
            if self.origins_XY_smoothed:
                bpy.data.objects.remove(bpy.data.objects[object_copy.name], do_unlink=True)
            prefs = bpy.context.preferences.addons[__name__].preferences
            if prefs.still_origin_override and prefs.still_origin or self.still_origin:
                bpy.data.objects[sel_obj].location.x = obj_locations_x
                bpy.data.objects[sel_obj].location.y = obj_locations_y
                bpy.data.objects[sel_obj].location.z = obj_locations_z
        
        
        # reset cursor position
        # bpy.context.scene.cursor.location = (0,0,0)
        # bpy.context.scene.cursor.rotation_euler = (0,0,0)

        # redo cursor transforms
        bpy.context.scene.cursor.location = orig_cursor_loc
        bpy.context.scene.cursor.rotation_euler = orig_cursor_rot
        
        # select objects again    
        for sel_obj in selected_obj:
            obj_origin = bpy.data.objects[sel_obj]
            obj_origin.select_set(True)
        
        ## get back to default
        # self.origins_axisX_prop = "Centered"
        # self.origins_axisY_prop = "Centered"
        # self.origins_axisZ_prop = "Floor"
        # self.origins_XY_smoothed = False
        
        print(f"{Addon_Name} done on : {str(selected_obj)} \n")
        print(f"\n {separator} {Addon_Name} Finished {separator} \n")
        
        return {"FINISHED"}     

# create keymap list
ootf_addon_keymaps = []

# list all classes
classes = (
    OOTF_Preferences,
    OBJECT_OT_ootf,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(originFloor_menu_draw)
    # add keymap
    if bpy.context.window_manager.keyconfigs.addon:
        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Window", space_type="EMPTY")
        keymapitem = keymap.keymap_items.new('object.origins_on_the_floor', #operator
                                             "DOWN_ARROW", #key
                                            "PRESS", # value
                                            ctrl=True, #alt=True
                                            )
        ootf_addon_keymaps.append((keymap, keymapitem))

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_object.remove(originFloor_menu_draw)
    # remove keymap
    for keymap, keymapitem in ootf_addon_keymaps:
        keymap.keymap_items.remove(keymapitem)
    ootf_addon_keymaps.clear()


if __name__ == "__main__":
    register()