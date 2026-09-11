// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"

class IVoxelEditorModule;

struct FVoxelInstallerUtilities
{
	static void DelayedCall(TFunction<void()> Call, float Delay = 0);
	static FString Unzip(const TArray64<uint8>& Data, TMap<FString, TArray64<uint8>>& OutFiles);
	static IVoxelEditorModule* GetEditorModule();
};