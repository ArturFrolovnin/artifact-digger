// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"
#include "VoxelPluginVersion.h"
#include "Widgets/Notifications/SNotificationList.h"

class FVoxelPluginDownload;

extern FVoxelPluginDownload* GVoxelAuthDownload;

class FVoxelPluginDownload
{
public:
	void Download(
		const FVoxelPluginVersion& Version,
		bool bInstallInEngine);

private:
	TSharedPtr<SNotificationItem> Notification;

	void Fail(const FString& Error);

	void FinalizeDownload(
		bool bInstallInEngine,
		const TArray<uint8>& Data,
		const FString& AesKey);

	void FinalizeDownloadImpl(
		bool bInstallInEngine,
		TArray64<uint8> Data,
		const FString& AesKey);

	static bool MakePathWriteable(FString Path);
};