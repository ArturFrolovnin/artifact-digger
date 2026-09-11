// Copyright Voxel Plugin SAS. All Rights Reserved.

using System;
using System.IO;
using UnrealBuildTool;

public class VoxelPluginInstaller : ModuleRules
{
    public VoxelPluginInstaller(ReadOnlyTargetRules Target) : base(Target)
    {
		//PCHUsage = ModuleRules.PCHUsageMode.NoPCHs;
        CppStandard = CppStandardVersion.Cpp20;

        // Marketplace requires third party deps to be in a ThirdParty folder
        PrivateIncludePaths.Add(ModuleDirectory + "/../ThirdParty");

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "Slate",
                "SlateCore",
                "InputCore",
                "HTTP",
                "Json",
                "Engine",
                "Projects",
                "ToolMenus",
                "ToolWidgets",
                "EditorStyle",
                "SettingsEditor",
                "DeveloperSettings",
                "GameProjectGeneration",
#if UE_5_4_OR_LATER
				"EventLoop",
#endif
	            "UnrealEd",
            });
    }
}