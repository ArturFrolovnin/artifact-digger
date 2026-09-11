// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "VoxelInstallerSettings.generated.h"

UCLASS(config = Engine, defaultconfig, meta = (DisplayName = "Voxel Installer"))
class UVoxelInstallerSettings : public UDeveloperSettings
{
    GENERATED_BODY()

public:
    UVoxelInstallerSettings()
    {
		CategoryName = "Plugins";
		SectionName = "Voxel Installer";
    }

	UPROPERTY(Config, EditAnywhere, Category = "Voxel Installer")
	bool bInstallInEngine = false;

	UPROPERTY(Config, EditAnywhere, Category = "Voxel Installer")
	bool bShowDevVersions = false;

	UPROPERTY(Config, EditAnywhere, Category = "Voxel Installer", meta = (EditCondition = "bShowDevVersions", EditConditionHides))
	bool bShowUnstableVersions = false;

	UPROPERTY(Config, EditAnywhere, Category = "Voxel Installer")
    int32 CacheSizeInMB = 1024;

	//~ Begin UDeveloperSettings Interface
	virtual FName GetContainerName() const override
	{
		return "Project";
	}
    //~ End UDeveloperSettings Interface
};