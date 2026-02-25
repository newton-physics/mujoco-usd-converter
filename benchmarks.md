# MuJoCo Menagerie Benchmark Report

**Generated on:** 2026-02-25 09:04:24

**Repository:** [https://github.com/google-deepmind/mujoco_menagerie.git](https://github.com/google-deepmind/mujoco_menagerie.git)

## Summary Statistics

| Total Models | Successful | Failed | Total Warnings | Total Errors | Average Time | Total Time | Total File Size |
|:------------:|:----------:|:------:|:--------------:|:------------:|:------------:|:----------:|:---------------:|
| 85 | 85 (100.0%) | 0 (0.0%) | 157 | 0 | 0.89s | 1m 15.29s | 395.73 MB |

## Detailed Results

| Asset | Variant | Success | [Verified (Manual)](#manual-annotation-instructions) | [Verified In Newton (Manual)](#manual-annotation-instructions) | Errors | Warnings | Time (s) | Size (MB) | Notes | Error Messages | Warning Messages |
|-------|---------|---------|----------|----------|-------:|--------:|---------:|---------:|----------------------|----------------|------------------|
| **[agilex_piper](https://github.com/google-deepmind/mujoco_menagerie/tree/main/agilex_piper/)** | piper | ✅ | ❌ | ❓ | 0 | 2 | 2.33 | 8.34 | Most actuation in MuJoCo looks good, but the gripper is broken without equality constraints |  | lights are not supported<br>keys are not supported |
| **[agility_cassie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/agility_cassie/)** | cassie | ✅ | ❓ | ❓ | 0 | 5 | 0.85 | 1.42 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'Ellipsoid'<br>cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[aloha](https://github.com/google-deepmind/mujoco_menagerie/tree/main/aloha/)** | aloha | ✅ | ❓ | ❓ | 0 | 3 | 0.64 | 3.05 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported |
| **[anybotics_anymal_b](https://github.com/google-deepmind/mujoco_menagerie/tree/main/anybotics_anymal_b/)** | anymal_b | ✅ | ❓ | ❓ | 0 | 1 | 1.71 | 5.00 |  |  | lights are not supported |
| **[anybotics_anymal_c](https://github.com/google-deepmind/mujoco_menagerie/tree/main/anybotics_anymal_c/)** | anymal_c | ✅ | ✅ | ❓ | 0 | 1 | 0.84 | 12.94 | Manual actuation in MuJoCo looks good |  | lights are not supported |
|  | anymal_c_mjx | ✅ | ❓ | ❓ | 0 | 2 | 0.70 | 12.87 |  |  | cameras are not supported<br>keys are not supported |
| **[apptronik_apollo](https://github.com/google-deepmind/mujoco_menagerie/tree/main/apptronik_apollo/)** | apptronik_apollo | ✅ | ❌ | ❓ | 0 | 4 | 1.26 | 28.54 | USD View looks good, and manual articulation in MuJoCo looks good, but without exclude pairs we cannot test actuation in MuJoCo as it falls through the ground plane |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[arx_l5](https://github.com/google-deepmind/mujoco_menagerie/tree/main/arx_l5/)** | arx_l5 | ✅ | ❓ | ❓ | 0 | 3 | 0.92 | 2.02 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported |
| **[berkeley_humanoid](https://github.com/google-deepmind/mujoco_menagerie/tree/main/berkeley_humanoid/)** | berkeley_humanoid | ✅ | ❓ | ❓ | 0 | 4 | 0.68 | 7.65 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[bitcraze_crazyflie_2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/bitcraze_crazyflie_2/)** | cf2 | ✅ | ❓ | ❓ | 0 | 3 | 0.51 | 0.26 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[booster_t1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/booster_t1/)** | t1 | ✅ | ❓ | ❓ | 0 | 3 | 0.61 | 3.15 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[boston_dynamics_spot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/boston_dynamics_spot/)** | spot | ✅ | ❓ | ❓ | 0 | 2 | 1.32 | 6.44 |  |  | lights are not supported<br>keys are not supported |
|  | spot_arm | ✅ | ❓ | ❓ | 0 | 2 | 1.57 | 8.72 |  |  | lights are not supported<br>keys are not supported |
| **[dynamixel_2r](https://github.com/google-deepmind/mujoco_menagerie/tree/main/dynamixel_2r/)** | dynamixel_2r | ✅ | ❓ | ❓ | 0 | 0 | 0.58 | 1.54 |  |  |  |
| **[flybody](https://github.com/google-deepmind/mujoco_menagerie/tree/main/flybody/)** | fruitfly | ✅ | ❓ | ❓ | 0 | 21 | 3.57 | 13.33 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'thorax_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'thorax_collision2'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'head_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rostrum_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'labrum_left_lower_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'labrum_right_lower_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_brown_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_membrane_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_fluid'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_brown_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_membrane_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_fluid'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T1_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T1_right_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T2_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T2_right_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T3_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T3_right_collision'<br>cameras are not supported<br>lights are not supported<br>sensors are not supported |
| **[fourier_n1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/fourier_n1/)** | n1 | ✅ | ❓ | ❓ | 0 | 2 | 1.04 | 19.57 |  |  | lights are not supported<br>sensors are not supported |
| **[franka_emika_panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda/)** | hand | ✅ | ❓ | ❓ | 0 | 0 | 0.51 | 0.43 |  |  |  |
|  | mjx_panda | ✅ | ❓ | ❓ | 0 | 1 | 1.22 | 6.92 |  |  | lights are not supported |
|  | mjx_panda_nohand | ✅ | ❓ | ❓ | 0 | 1 | 1.14 | 6.49 |  |  | lights are not supported |
|  | panda | ✅ | ❓ | ❓ | 0 | 2 | 1.23 | 6.93 |  |  | lights are not supported<br>keys are not supported |
|  | panda_nohand | ✅ | ❓ | ❓ | 0 | 2 | 1.15 | 6.50 |  |  | lights are not supported<br>keys are not supported |
| **[franka_fr3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_fr3/)** | fr3 | ✅ | ✅ | ❓ | 0 | 1 | 1.14 | 7.37 | Manual actuation in MuJoCo looks good |  | keys are not supported |
| **[google_barkour_v0](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_barkour_v0/)** | barkour_v0 | ✅ | ✅ | ❓ | 0 | 3 | 0.54 | 3.48 | Manual actuation in MuJoCo looks good |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
|  | barkour_v0_mjx | ✅ | ❓ | ❓ | 0 | 3 | 0.55 | 3.49 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[google_barkour_vb](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_barkour_vb/)** | barkour_vb | ✅ | ❓ | ❓ | 0 | 2 | 0.51 | 1.66 |  |  | cameras are not supported<br>sensors are not supported |
|  | barkour_vb_mjx | ✅ | ❓ | ❓ | 0 | 2 | 0.51 | 1.65 |  |  | cameras are not supported<br>sensors are not supported |
| **[google_robot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_robot/)** | robot | ✅ | ❓ | ❓ | 0 | 1 | 0.63 | 2.82 |  |  | lights are not supported |
| **[hello_robot_stretch](https://github.com/google-deepmind/mujoco_menagerie/tree/main/hello_robot_stretch/)** | stretch | ✅ | ❓ | ❓ | 0 | 1 | 2.18 | 11.93 |  |  | cameras are not supported |
| **[hello_robot_stretch_3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/hello_robot_stretch_3/)** | stretch | ✅ | ❓ | ❓ | 0 | 3 | 2.27 | 12.80 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[i2rt_yam](https://github.com/google-deepmind/mujoco_menagerie/tree/main/i2rt_yam/)** | yam | ✅ | ❓ | ❓ | 0 | 2 | 0.55 | 1.78 |  |  | lights are not supported<br>keys are not supported |
| **[iit_softfoot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/iit_softfoot/)** | softfoot | ✅ | ❓ | ❓ | 0 | 0 | 0.96 | 2.08 |  |  |  |
| **[kinova_gen3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/kinova_gen3/)** | gen3 | ✅ | ❓ | ❓ | 0 | 2 | 0.46 | 1.60 |  |  | cameras are not supported<br>keys are not supported |
| **[kuka_iiwa_14](https://github.com/google-deepmind/mujoco_menagerie/tree/main/kuka_iiwa_14/)** | iiwa14 | ✅ | ❓ | ❓ | 0 | 2 | 0.63 | 1.42 |  |  | lights are not supported<br>keys are not supported |
| **[leap_hand](https://github.com/google-deepmind/mujoco_menagerie/tree/main/leap_hand/)** | left_hand | ✅ | ❓ | ❓ | 0 | 3 | 0.93 | 2.57 |  |  | "distal.obj" contains multiple meshes, only the first one will be converted<br>"thumb_distal.obj" contains multiple meshes, only the first one will be converted<br>sensors are not supported |
|  | right_hand | ✅ | ❓ | ❓ | 0 | 3 | 0.84 | 2.15 |  |  | "distal.obj" contains multiple meshes, only the first one will be converted<br>"thumb_distal.obj" contains multiple meshes, only the first one will be converted<br>sensors are not supported |
| **[low_cost_robot_arm](https://github.com/google-deepmind/mujoco_menagerie/tree/main/low_cost_robot_arm/)** | low_cost_robot_arm | ✅ | ❓ | ❓ | 0 | 1 | 0.53 | 2.33 |  |  | keys are not supported |
| **[pal_talos](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_talos/)** | talos | ✅ | ❓ | ❓ | 0 | 0 | 0.81 | 3.45 |  |  |  |
|  | talos_motor | ✅ | ❓ | ❓ | 0 | 1 | 0.82 | 3.46 |  |  | keys are not supported |
|  | talos_position | ✅ | ❓ | ❓ | 0 | 1 | 0.82 | 3.47 |  |  | keys are not supported |
| **[pal_tiago](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_tiago/)** | tiago | ✅ | ❓ | ❓ | 0 | 1 | 0.55 | 2.14 |  |  | cameras are not supported |
|  | tiago_motor | ✅ | ❓ | ❓ | 0 | 1 | 0.55 | 2.15 |  |  | cameras are not supported |
|  | tiago_position | ✅ | ❓ | ❓ | 0 | 2 | 0.55 | 2.15 |  |  | cameras are not supported<br>keys are not supported |
|  | tiago_velocity | ✅ | ❓ | ❓ | 0 | 2 | 0.57 | 2.15 |  |  | cameras are not supported<br>keys are not supported |
| **[pal_tiago_dual](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_tiago_dual/)** | tiago_dual | ✅ | ❓ | ❓ | 0 | 0 | 0.62 | 2.71 |  |  |  |
|  | tiago_dual_motor | ✅ | ❓ | ❓ | 0 | 0 | 0.61 | 2.72 |  |  |  |
|  | tiago_dual_position | ✅ | ❓ | ❓ | 0 | 0 | 0.63 | 2.72 |  |  |  |
|  | tiago_dual_velocity | ✅ | ❓ | ❓ | 0 | 0 | 0.61 | 2.72 |  |  |  |
| **[pndbotics_adam_lite](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pndbotics_adam_lite/)** | adam_lite | ✅ | ❓ | ❓ | 0 | 0 | 3.74 | 22.17 |  |  |  |
| **[realsense_d435i](https://github.com/google-deepmind/mujoco_menagerie/tree/main/realsense_d435i/)** | d435i | ✅ | ❓ | ❓ | 0 | 1 | 2.72 | 7.73 |  |  | lights are not supported |
| **[rethink_robotics_sawyer](https://github.com/google-deepmind/mujoco_menagerie/tree/main/rethink_robotics_sawyer/)** | sawyer | ✅ | ❓ | ❓ | 0 | 2 | 1.17 | 6.67 |  |  | lights are not supported<br>keys are not supported |
| **[robot_soccer_kit](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robot_soccer_kit/)** | robot_soccer_kit | ✅ | ❓ | ❓ | 0 | 0 | 1.06 | 2.49 |  |  |  |
| **[robotiq_2f85](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotiq_2f85/)** | 2f85 | ✅ | ❓ | ❓ | 0 | 0 | 0.50 | 1.03 |  |  |  |
| **[robotiq_2f85_v4](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotiq_2f85_v4/)** | 2f85 | ✅ | ❓ | ❓ | 0 | 0 | 0.50 | 1.93 |  |  |  |
|  | mjx_2f85 | ✅ | ❓ | ❓ | 0 | 0 | 0.49 | 1.92 |  |  |  |
| **[robotis_op3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotis_op3/)** | op3 | ✅ | ❓ | ❓ | 0 | 2 | 0.88 | 11.26 |  |  | cameras are not supported<br>lights are not supported |
| **[shadow_dexee](https://github.com/google-deepmind/mujoco_menagerie/tree/main/shadow_dexee/)** | shadow_dexee | ✅ | ❓ | ❓ | 0 | 2 | 0.71 | 2.30 |  |  | lights are not supported<br>sensors are not supported |
| **[shadow_hand](https://github.com/google-deepmind/mujoco_menagerie/tree/main/shadow_hand/)** | left_hand | ✅ | ❓ | ❓ | 0 | 0 | 0.61 | 0.93 |  |  |  |
|  | right_hand | ✅ | ❓ | ❓ | 0 | 0 | 0.62 | 0.93 |  |  |  |
| **[skydio_x2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/skydio_x2/)** | x2 | ✅ | ❓ | ❓ | 0 | 9 | 0.44 | 0.39 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor1'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor2'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor3'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor4'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'Ellipsoid'<br>cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[stanford_tidybot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/stanford_tidybot/)** | base | ✅ | ❓ | ❓ | 0 | 0 | 0.43 | 0.09 |  |  |  |
|  | tidybot | ✅ | ❓ | ❓ | 0 | 2 | 0.58 | 2.44 |  |  | cameras are not supported<br>keys are not supported |
| **[trossen_vx300s](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trossen_vx300s/)** | vx300s | ✅ | ❓ | ❓ | 0 | 2 | 0.51 | 0.51 |  |  | lights are not supported<br>keys are not supported |
| **[trossen_wx250s](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trossen_wx250s/)** | wx250s | ✅ | ❓ | ❓ | 0 | 2 | 0.46 | 0.26 |  |  | lights are not supported<br>keys are not supported |
| **[trs_so_arm100](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trs_so_arm100/)** | so_arm100 | ✅ | ❓ | ❓ | 0 | 1 | 0.49 | 1.02 |  |  | keys are not supported |
| **[ufactory_lite6](https://github.com/google-deepmind/mujoco_menagerie/tree/main/ufactory_lite6/)** | lite6 | ✅ | ❓ | ❓ | 0 | 1 | 0.46 | 1.21 |  |  | keys are not supported |
|  | lite6_gripper_narrow | ✅ | ❓ | ❓ | 0 | 1 | 0.49 | 1.38 |  |  | keys are not supported |
|  | lite6_gripper_wide | ✅ | ❓ | ❓ | 0 | 1 | 0.50 | 1.40 |  |  | keys are not supported |
| **[ufactory_xarm7](https://github.com/google-deepmind/mujoco_menagerie/tree/main/ufactory_xarm7/)** | hand | ✅ | ❓ | ❓ | 0 | 0 | 0.45 | 0.71 |  |  |  |
|  | xarm7 | ✅ | ❓ | ❓ | 0 | 1 | 0.50 | 1.52 |  |  | keys are not supported |
|  | xarm7_nohand | ✅ | ❓ | ❓ | 0 | 1 | 0.44 | 0.79 |  |  | keys are not supported |
| **[umi_gripper](https://github.com/google-deepmind/mujoco_menagerie/tree/main/umi_gripper/)** | umi_gripper | ✅ | ❓ | ❓ | 0 | 3 | 0.48 | 0.76 |  |  | Binding a textured Material '/umi_gripper/Materials/Left_Aruco_Base_Sticker' to a Cube Prim ('/umi_gripper/Geometry/Body/left_finger_holder/left_marker') will discard textures at render time.<br>Binding a textured Material '/umi_gripper/Materials/Right_Aruco_Base_Sticker' to a Cube Prim ('/umi_gripper/Geometry/Body/right_finger_holder/right_marker') will discard textures at render time.<br>cameras are not supported |
| **[unitree_a1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_a1/)** | a1 | ✅ | ❓ | ❓ | 0 | 2 | 0.90 | 4.00 |  |  | lights are not supported<br>keys are not supported |
| **[unitree_g1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_g1/)** | g1 | ✅ | ❓ | ❓ | 0 | 3 | 0.78 | 7.87 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
|  | g1_mjx | ✅ | ❓ | ❓ | 0 | 3 | 0.73 | 7.85 |  |  | cameras are not supported<br>lights are not supported<br>sensors are not supported |
|  | g1_with_hands | ✅ | ❓ | ❓ | 0 | 3 | 0.92 | 10.56 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[unitree_go1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_go1/)** | go1 | ✅ | ❓ | ❓ | 0 | 3 | 0.60 | 2.74 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported |
| **[unitree_go2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_go2/)** | go2 | ✅ | ❓ | ❓ | 0 | 1 | 1.18 | 6.33 |  |  | keys are not supported |
|  | go2_mjx | ✅ | ❓ | ❓ | 0 | 3 | 1.23 | 6.34 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[unitree_h1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_h1/)** | h1 | ✅ | ❓ | ❓ | 0 | 1 | 0.65 | 5.44 |  |  | lights are not supported |
| **[unitree_z1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_z1/)** | z1 | ✅ | ❓ | ❓ | 0 | 1 | 0.53 | 3.41 |  |  | keys are not supported |
|  | z1_gripper | ✅ | ❓ | ❓ | 0 | 1 | 0.60 | 4.72 |  |  | keys are not supported |
| **[universal_robots_ur10e](https://github.com/google-deepmind/mujoco_menagerie/tree/main/universal_robots_ur10e/)** | ur10e | ✅ | ❓ | ❓ | 0 | 2 | 1.10 | 6.54 |  |  | lights are not supported<br>keys are not supported |
| **[universal_robots_ur5e](https://github.com/google-deepmind/mujoco_menagerie/tree/main/universal_robots_ur5e/)** | ur5e | ✅ | ❓ | ❓ | 0 | 2 | 1.08 | 6.11 |  |  | lights are not supported<br>keys are not supported |
| **[wonik_allegro](https://github.com/google-deepmind/mujoco_menagerie/tree/main/wonik_allegro/)** | left_hand | ✅ | ❓ | ❓ | 0 | 0 | 0.51 | 0.50 |  |  |  |
|  | right_hand | ✅ | ❓ | ❓ | 0 | 0 | 0.51 | 0.40 |  |  |  |


## Manual Annotation Instructions

### Verified Status
Each model variant can be individually annotated with "Yes", "No", or "Unknown" based on manual
inspection of the converted USD files. Update the annotations in the `tools/menagerie_annotations.yaml`
file under each variant's `verified` field.

**Consider these factors:**
- Visual correctness when loaded in USD viewer
- Proper hierarchy and naming
- Material and texture fidelity
- Physics properties preservation
- Simulation correctness in MuJoCo Simulate compared to the original MJCF file

### Verified In Newton Status
The results of verifying the converted USD file in the Newton runtime will be annotated as "Yes", "No", or "Unknown".
Update the annotations in the `tools/menagerie_annotations.yaml` file under each variant's `verified_in_newton` field.

**Please follow the steps below to verify:**
- Convert MJCF to USD
- Load each into an instance of mujoco Simulate app
- Pause & manually move the joints
- Run & manually activate the actuators
- Inspect results visually & determine if they appear identical
- Annoate the column in the report
  - If not yet checked, specify "Unknown"
  - If the result is correct, specify "Yes"
  - If the result is incorrect, specify "No"

### Notes
Document any known issues, limitations, or special considerations for each model variant in the
`notes` field under each variant in the annotations file.

### Annotation Structure
Annotations are per-variant rather than per-asset. Each XML file listed under an asset's
`xml_files` array has its own `verified`, `notes`, `evaluation_date`, `evaluator`, and `notes` fields.

### File Size Information
**Total Size:** Overall size of all files in the output directory, including USD files, textures,
and any other generated assets.

---

*Report generated by mujoco-usd-converter benchmark tool*
