import bpy
import bpycv
import cv2
import addon_utils
import numpy as np


card_dir = "/Users/js5013/programs/prosthetic/set/cards/"
save_dir = "/Users/js5013/programs/prosthetic/set/data/"
n_gen = 100
n_cards = 10
replace = False


## enable dynamic sky and import image as planes addons
addon_names = ["io_import_images_as_planes"]
for addon in addon_names:
    loaded_default, loaded_state = addon_utils.check(addon)
    if not loaded_state:
        addon_utils.enable(addon)

# delete everything
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# add background plane
bpy.ops.mesh.primitive_plane_add(size=25)

ixs = np.random.choice(np.arange(1, 82), size=n_cards, replace=replace)
for ix in ixs:
    i = int(ix)  # weird but it doesn't work without this line...
    cname = f"card-{i}"
    path = f"{card_dir}/{cname}.jpg"
    bpy.ops.import_image.to_plane(files=[{"name": path}])
    card = bpy.data.objects[cname]
    card.location = (0, 0, 0.03)
    card.dimensions = (0.2, 0.4, 0)  # a big card!
    card["inst_id"] = i

# add a light
light_data = bpy.data.lights.new("light", type="POINT")
light = bpy.data.objects.new("light", light_data)
bpy.context.collection.objects.link(light)
light.location = (1, 2, 1.5)  # meters away
light.data.energy = 120.0  # watts
light.data.shadow_soft_size = 0.2  # radius of lightbulb in m

# make camera
cam_data = bpy.data.cameras.new("camera")
cam = bpy.data.objects.new("camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (-2, 2, 1.5)
cam.data.lens = 50

constraint = cam.constraints.new(type="TRACK_TO")
constraint.target = bpy.data.objects["Plane"]

scene = bpy.context.scene
scene.camera = cam
scene.render.image_settings.file_format = "JPEG"
scene.eevee.taa_render_samples = 32

for it in range(n_gen):
    cam.location = (*np.random.normal(size=2), np.random.uniform(1, 3, size=1))
    cam.data.lens = np.random.uniform(24, 50)
    light.data.energy = np.random.uniform(100, 500)  # watts
    light.data.shadow_soft_size = np.random.uniform(0, 2)  # radius of lightbulb in m
    light.data.color = np.random.uniform(0.8, 1, size=3)  # random color, bright-ish
    for ix in ixs:
        cname = f"card-{ix}"
        card = bpy.data.objects[cname]
        card.rotation_euler[2] = np.random.uniform(0, 2 * np.pi)  # random rotation
        card.location[:2] = np.random.uniform(-1.0, 1.0, size=2)
        card.location[2] = np.random.uniform(1e-5, 0.03)  # random height

    result = bpycv.render_data()
    inst = result["inst"]

    out_string = ""

    for ix in ixs:
        y, x = np.where(inst == ix)
        try:
            x_width, y_width = x.max() - x.min(), y.max() - y.min()
            x_center, y_center = (x.min() + x.max()) / 2, (y.min() + y.max()) / 2
            x_width, x_center = x_width / inst.shape[1], x_center / inst.shape[1]
            y_width, y_center = y_width / inst.shape[0], y_center / inst.shape[0]
            out_string += f"{ix} {x_center} {y_center} {x_width} {y_width}\n"
        except:
            pass

    with open(f"{save_dir}/ims/im-{it}.txt", "w") as f:
        f.write(out_string)

    cv2.imwrite(f"{save_dir}/ims/im-{it}.jpg", result["image"][..., ::-1])
    cv2.imwrite(f"{save_dir}/inst/inst-{it}.jpg", inst * 255 / inst.max())
