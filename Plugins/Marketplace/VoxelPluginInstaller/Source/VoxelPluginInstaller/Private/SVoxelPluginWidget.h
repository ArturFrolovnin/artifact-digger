// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"
#include "VoxelPluginApi.h"
#include "Widgets/SCompoundWidget.h"

class SButton;

class SVoxelPluginWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SVoxelPluginWidget) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& Args);

private:
	static TSharedRef<SWidget> MakeHeaderSection();
	static TSharedRef<SWidget> MakeUserSection();
	TSharedRef<SWidget> MakeInstalledVersionsSection();
	TSharedRef<SWidget> MakeInstallPluginSection();

private:
	static TSharedRef<SButton> MakeLoginButton();
	static TSharedRef<SButton> MakeURLIconButton(const FString& ToolTip, const FString& URL, const FSlateBrush* Icon);

private:
	TArray<TSharedPtr<FVoxelPluginApi::FPluginInfo>> InstalledPlugins;
	TArray<TSharedPtr<FString>> AvailablePluginVersions;
};