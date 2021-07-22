bl_info = {
    "name": "GMEHelper",
    "version": (0, 1),
    "author": "KendricKUrieL",
    "description": "Automated texture loading and material assigning script for HS1",
    "blender": (2, 93, 1),
    "category" : "Material",
    "support": "TESTING"
}

import glob
import bpy
from bpy import types
from bpy import utils
from bpy import props
from bpy import data
from bpy import path

suffixes = [
    "_MainTex",
    "_OcclusionMap",
    "_SpecGlossMap",
    "_BumpMap",
    "_BlendNormalMap",
    "_DetailNormalMap",
    "_EmissionMap"
    ]

location = {
    "_MainTex": (-1000, 800),
    "_OcclusionMap": (-1000, 500),
    "_SpecGlossMap": (-1000, 200),
    "_BumpMap": (-1000, -200),
    "_BlendNormalMap": (-1000, -500),
    "_DetailNormalMap": (-1000, -800),
    "_EmissionMap": (-1300, 0)
    }

class MainPanel(types.Panel):
    bl_idname = "UI_PT_main_panel"
    bl_label = "GMEHelper"
    bl_category = "GMEHelper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
        
    def draw(self, context):    
        self.layout.row(align = True).operator("op.remove_empties", text = "Remove Empty Slots")
        self.layout.row(align = True).separator()
        self.layout.row(align = True).label(text = "Choose textures folder first!")
        self.layout.row(align = True).prop(context.scene.my_tool, "path", text = "")
        self.layout.row(align = True).operator("op.assign_materials")
        
        self.layout.row(align = True).separator()
        self.layout.row(align = True).operator("op.create_template")
        
class RemoveEmpties(types.Operator):
    bl_idname = "op.remove_empties"
    bl_label = "Remove Empty Slots"
    
    def search(self, context):
        return [obj for obj in data.objects if obj.type.startswith("EMPTY") and not obj.children]
    
    def execute(self, context):
        while [] != self.search(context):
            empties = self.search(context)
            while empties:
                data.objects.remove(empties.pop())
        return {"FINISHED"}
    
class TexturesPath(types.PropertyGroup):
    path : props.StringProperty(default = "", maxlen = 4096, subtype = "DIR_PATH")


class AssignMaterials(types.Operator):
    bl_idname = "op.assign_materials"
    bl_label = "Assign Basic Materials"
    
    def assign(self, context, material, query, sg_alpha):
        build = MaterialBuilder(context, material)
        build.LoadTextures(query)
        build.AlbedoOcclusion()
        build.SpecGloss(sg_alpha)
        build.NormalMaps()
        
    def execute(self, context):
        # Body
        material = data.materials.new(name = "body")
        self.assign(context, material, query = "cf_m_body", sg_alpha = False)
        ObjectSearch(context, "cf_O_body").active_material = material
        ObjectSearch(context, "cf_O_unc").active_material = material
        
        # Head
        material = data.materials.new(name = "head")
        self.assign(context, material, query = "cf_m_face", sg_alpha = False)
        data.objects["cf_O_head"].active_material = material
        
        # Eyebrows
        material = data.materials.new(name = "eyebrows")
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        self.assign(context, material, query = "cf_m_eyebrow", sg_alpha = True)
        data.objects["cf_O_mayuge"].active_material = material
                
        # Eyelashes
        material = data.materials.new(name = "eyelashes")
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        self.assign(context, material, query = "cf_m_eyelashes", sg_alpha = True)
        data.objects["cf_O_matuge"].active_material = material
        
        # Eye whites
        material = data.materials.new(name = "eyewhites")
        self.assign(context, material, query = "cf_M_eyewhite", sg_alpha = True)
        data.objects["cf_O_eyewhite_L"].active_material = material
        data.objects["cf_O_eyewhite_R"].active_material = material
                
        # Eye pupils
        material = data.materials.new(name = "eyepupils")
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        self.assign(context, material, query = "cf_M_eye_", sg_alpha = True)
        data.objects["cf_O_eye_L"].active_material = material
        data.objects["cf_O_eye_R"].active_material = material
        
        # Eye highlights
        material = data.materials.new(name = "eyehighlights")
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        self.assign(context, material, query = "cf_M_eyehi", sg_alpha = True)
        data.objects["cf_O_eyehikari_L"].active_material = material
        data.objects["cf_O_eyehikari_R"].active_material = material
        
        # Eye kages (?)
        material = data.materials.new(name = "eyekages")
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        self.assign(context, material, query = "cf_M_eyekage", sg_alpha = True)
        data.objects["cf_O_eyekage1"].active_material = material
        
        # Teeth
        material = data.materials.new(name = "teeth")
        self.assign(context, material, query = "cf_M_tooth", sg_alpha = True)
        data.objects["cf_O_ha"].active_material = material
        
        # Tongue
        material = data.materials.new(name = "tongue")
        self.assign(context, material, query = "cf_M_tang", sg_alpha = True)
        data.objects["cf_O_sita"].active_material = material
        
        # Nails
        material = data.materials.new(name = "nails")
        self.assign(context, material, query = "cf_M_nail", sg_alpha = True)
        data.objects["cf_O_nail"].active_material = material
            
        return {"FINISHED"}
    
class MaterialBuilder():
    def __init__(self, context, material):
        self.context = context
        self.material = material
        self.material.use_nodes = True
        self.shader = self.material.node_tree.nodes.get("Principled BSDF")
        
    def TextureSearch(self, query):
        abs = path.abspath(self.context.scene.my_tool.path).replace("\\", "/")
        ans = glob.glob(abs + query + "*.png")
        print(ans)
        
        if [] != ans:
            ans = ans[0].replace("\\", "/").split("/")[-1]
            ans = ans.removesuffix(".png")
            
            for suffix in suffixes:
                ans = ans.removesuffix(suffix)
                
            return ans
        
    def LoadTextures(self, query):
        texture = {}
        self.node = {}
        
        prefix = self.TextureSearch(query)
        
        for suffix in suffixes:
            try:
                texture[suffix] = data.images.load(self.context.scene.my_tool.path + prefix + suffix + ".png")
                texture[suffix].colorspace_settings.name = "Raw"
                
                self.node[suffix] = self.material.node_tree.nodes.new("ShaderNodeTexImage")
                self.node[suffix].image = texture[suffix]
                self.node[suffix].location = location[suffix]
                
            except:
                None
                
    def AlbedoOcclusion(self):
        clr = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
        clr.blend_type = "MULTIPLY"
        clr.inputs[0].default_value = 1
        clr.inputs[2].default_value = (1, 1, 1, 1)
        clr.location = (-250, 650)
        self.material.node_tree.links.new(clr.outputs[0], self.shader.inputs[0])
        
        if "_MainTex" in self.node and "_OcclusionMap" in self.node:
            mix = self.material.node_tree.nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1
            mix.location = (-650, 650)
            
            self.material.node_tree.links.new(self.node["_MainTex"].outputs[0], mix.inputs[1])
            self.material.node_tree.links.new(self.node["_OcclusionMap"].outputs[0], mix.inputs[2])
            self.material.node_tree.links.new(mix.outputs[0], clr.inputs[1])
            self.material.node_tree.links.new(self.node["_MainTex"].outputs[1], self.shader.inputs[19])
            
        elif "_MainTex" in self.node:
            self.material.node_tree.links.new(self.node["_MainTex"].outputs[0], clr.inputs[1])
            self.material.node_tree.links.new(self.node["_MainTex"].outputs[1], self.shader.inputs[19])
        
        elif "_OcclusionMap" in self.node:
            self.material.node_tree.links.new(self.node["_OcclusionMap"].outputs[0], clr.inputs[1])
            
    def SpecGloss(self, alpha = False):
        if "_SpecGlossMap" in self.node:
            spec = self.material.node_tree.nodes.new("ShaderNodeMath")
            spec.operation = "MULTIPLY"
            spec.location = (-650, 300)
            gloss = self.material.node_tree.nodes.new("ShaderNodeMath")
            gloss.operation = "MULTIPLY"
            gloss.location = (-650, 100)
            rough = self.material.node_tree.nodes.new("ShaderNodeInvert")
            rough.inputs[0].default_value = 1
            rough.location = (-250, 100)
            
            self.material.node_tree.links.new(self.node["_SpecGlossMap"].outputs[0], spec.inputs[0])
            self.material.node_tree.links.new(spec.outputs[0], self.shader.inputs[5])
            
            if alpha:
                self.material.node_tree.links.new(self.node["_SpecGlossMap"].outputs[1], gloss.inputs[0])
                
            else:
                self.material.node_tree.links.new(self.node["_SpecGlossMap"].outputs[0], gloss.inputs[0])
                
            self.material.node_tree.links.new(gloss.outputs[0], rough.inputs[1])
            self.material.node_tree.links.new(rough.outputs[0], self.shader.inputs[7])
                
    def NormalMaps(self):
        if "_BumpMap" in self.node:
            bump = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
            bump.location = (-650, -200)
            bump.inputs[0].default_value = 1.0
            self.material.node_tree.links.new(self.node["_BumpMap"].outputs[0], bump.inputs[1])
            
        if "_BlendNormalMap" in self.node:
            blend = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
            blend.location = (-650, -500)
            blend.inputs[0].default_value = 1.0
            self.material.node_tree.links.new(self.node["_BlendNormalMap"].outputs[0], blend.inputs[1])
            
        if "_DetailNormalMap" in self.node:
            detail = self.material.node_tree.nodes.new("ShaderNodeNormalMap")
            detail.location = (-650, -800)
            detail.inputs[0].default_value = 1.0
            self.material.node_tree.links.new(self.node["_DetailNormalMap"].outputs[0], detail.inputs[1])
            
        if "_BumpMap" in self.node and "_BlendNormalMap" in self.node and "_DetailNormalMap" in self.node:
            mix1 = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
            mix1.operation = "ADD"
            mix1.location = (-250, -200)
            mix2 = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
            mix2.operation = "ADD"
            mix2.location = (-400, -500)
            
            self.material.node_tree.links.new(bump.outputs[0], mix1.inputs[0])
            self.material.node_tree.links.new(mix2.outputs[0], mix1.inputs[1])
            self.material.node_tree.links.new(blend.outputs[0], mix2.inputs[0])
            self.material.node_tree.links.new(detail.outputs[0], mix2.inputs[1])
            
            self.material.node_tree.links.new(mix1.outputs[0], self.shader.inputs[20])
            
        elif "_BumpMap" in self.node and "_BlendNormalMap" in self.node:
            mix = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
            mix.operation = "ADD"
            mix.location = (-250, -200)
            self.material.node_tree.links.new(bump.outputs[0], mix.inputs[0])
            self.material.node_tree.links.new(blend.outputs[0], mix.inputs[1])
            self.material.node_tree.links.new(mix.outputs[0], self.shader.inputs[20])
            
        elif "_BumpMap" in self.node and "_DetailNormalMap" in self.node:
            mix = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
            mix.operation = "ADD"
            mix.location = (-250, -200)
            self.material.node_tree.links.new(bump.outputs[0], mix.inputs[0])
            self.material.node_tree.links.new(detail.outputs[0], mix.inputs[1])
            self.material.node_tree.links.new(mix.outputs[0], self.shader.inputs[20])
            
        elif "_BlendNormalMap" in self.node and "_DetailNormalMap" in self.node:
            mix = self.material.node_tree.nodes.new("ShaderNodeVectorMath")
            mix.operation = "ADD"
            mix.location = (-250, -200)
            self.material.node_tree.links.new(blend.outputs[0], mix.inputs[0])
            self.material.node_tree.links.new(detail.outputs[0], mix.inputs[1])
            self.material.node_tree.links.new(mix.outputs[0], self.shader.inputs[20])
            
        elif "_BumpMap" in self.node:
            self.material.node_tree.links.new(bump.outputs[0], self.shader.inputs[20])
            
        elif "_BlendNormalMap" in self.node:
            self.material.node_tree.links.new(blend.outputs[0], self.shader.inputs[20])
            
        elif "_DetailNormalMap" in self.node:
            self.material.node_tree.links.new(detail.outputs[0], self.shader.inputs[20])
            
class CreateTemplate(types.Operator):
    bl_idname = "op.create_template"
    bl_label = "Create Material Template"
    
    def execute(self, context):
        material = data.materials.new(name = "template")
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        node = {}
        
        for suffix in suffixes:
            node[suffix] = material.node_tree.nodes.new("ShaderNodeTexImage")
            node[suffix].location = location[suffix]
            
        clr = material.node_tree.nodes.new("ShaderNodeMixRGB")
        clr.blend_type = "MULTIPLY"
        clr.inputs[0].default_value = 1
        clr.inputs[2].default_value = (1, 1, 1, 1)
        clr.location = (-250, 650)
        
        occ = material.node_tree.nodes.new("ShaderNodeMixRGB")
        occ.blend_type = "MULTIPLY"
        occ.inputs[0].default_value = 1
        occ.location = (-650, 650)
        
        spec = material.node_tree.nodes.new("ShaderNodeMath")
        spec.operation = "MULTIPLY"
        spec.location = (-650, 300)
        
        gloss = material.node_tree.nodes.new("ShaderNodeMath")
        gloss.operation = "MULTIPLY"
        gloss.location = (-650, 100)
        
        rough = material.node_tree.nodes.new("ShaderNodeInvert")
        rough.inputs[0].default_value = 1
        rough.location = (-250, 100)
        
        bump = material.node_tree.nodes.new("ShaderNodeNormalMap")
        bump.location = (-650, -200)
        bump.inputs[0].default_value = 1.0
        
        blend = material.node_tree.nodes.new("ShaderNodeNormalMap")
        blend.location = (-650, -500)
        blend.inputs[0].default_value = 1.0
        
        detail = material.node_tree.nodes.new("ShaderNodeNormalMap")
        detail.location = (-650, -800)
        detail.inputs[0].default_value = 1.0
        
        add1 = material.node_tree.nodes.new("ShaderNodeVectorMath")
        add1.operation = "ADD"
        add1.location = (-250, -200)
        
        add2 = material.node_tree.nodes.new("ShaderNodeVectorMath")
        add2.operation = "ADD"
        add2.location = (-400, -500)
            
        return {"FINISHED"}

def ObjectSearch(context, prefix):
    for obj in context.editable_objects:
        if obj.name.startswith(prefix):
            return obj
            
classes = [
    MainPanel,
    RemoveEmpties,
    TexturesPath,
    AssignMaterials,
    CreateTemplate
]

def register():
    for cls in classes:
        utils.register_class(cls)
        
    types.Scene.my_tool = props.PointerProperty(type = TexturesPath)

def unregister():
    for cls in classes:
        utils.unregister_class(cls)
        
    del types.Scene.my_tool

if __name__ == "__main__":
    register()