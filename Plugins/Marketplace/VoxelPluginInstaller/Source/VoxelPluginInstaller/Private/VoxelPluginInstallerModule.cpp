// Copyright Voxel Plugin SAS. All Rights Reserved.

#include "VoxelMinimal.h"
#include "VoxelPluginApi.h"
#include "SVoxelPluginWidget.h"
#include "VoxelPluginDownload.h"
#include "VoxelInstallerUtilities.h"
#include "HttpModule.h"
#include "HttpManager.h"
#include "ToolMenus.h"
#include "Misc/CommandLine.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleRegistry.h"
#include "Interfaces/IPluginManager.h"
#include "Runtime/Online/HTTP/Private/HttpThread.h"

DEFINE_PRIVATE_ACCESS(FHttpManager, bUseEventLoop)
DEFINE_PRIVATE_ACCESS(FLegacyHttpThread, HttpThreadActiveFrameTimeInSeconds)

TSharedRef<SWidget> GenerateVoxelMenuWidget()
{
	return SNew(SVoxelPluginWidget);
}

FSlateStyleSet* GVoxelPluginInstallerStyle = nullptr;

class FVoxelPluginInstallerModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		// Increase the HTTP tick rate
		// Makes downloads much faster
		INLINE_LAMBDA
		{
			FHttpManager& HttpManager = FHttpModule::Get().GetHttpManager();
			if (PrivateAccess::bUseEventLoop(HttpManager))
			{
				return;
			}

			UE_LOG(LogVoxelInstaller, Display, TEXT("Increasing HTTP Tick Rate"));

			FHttpThreadBase* Thread = HttpManager.GetThread();
			if (!Thread)
			{
				return;
			}

			FLegacyHttpThread* LegacyThread = static_cast<FLegacyHttpThread*>(Thread);
			PrivateAccess::HttpThreadActiveFrameTimeInSeconds(*LegacyThread) = 1 / 100000.f;
		};

		GVoxelPluginInstallerStyle = new FSlateStyleSet("VoxelPluginInstallerStyle");
		GVoxelPluginInstallerStyle->SetContentRoot(IPluginManager::Get().FindPlugin("VoxelPluginInstaller")->GetBaseDir() / TEXT("Resources"));

#define ICON(Name, Size) GVoxelPluginInstallerStyle->Set(Name, new FSlateImageBrush(GVoxelPluginInstallerStyle->RootToContentDir(TEXT(Name), TEXT(".png")), FVector2D(Size)));
		ICON("DiscordIcon", 64.f);
		ICON("EmailIcon", 32.f);
		ICON("VoxelIcon", 16.f);
		ICON("VoxelIconWithUpdate", 16.f);
#undef ICON

#define ICON(Name, Size) GVoxelPluginInstallerStyle->Set(Name, new FSlateVectorImageBrush(GVoxelPluginInstallerStyle->RootToContentDir(TEXT(Name), TEXT(".svg")), FVector2D(Size)));
		ICON("AccountIcon", 16.f);
#undef ICON

#define BOX_BRUSH(RelativePath, ...) FSlateBoxBrush(FPaths::EngineContentDir() / "Editor" / "Slate" / RelativePath + ".png", __VA_ARGS__)

		GVoxelPluginInstallerStyle->Set("EpicButton", FButtonStyle()
			.SetNormal(BOX_BRUSH("Common/FlatButton", 2.0f / 8.0f, FLinearColor(0.007843f, 0.007843f, 0.007843f)))
			.SetHovered(BOX_BRUSH("Common/FlatButton", 2.0f / 8.0f, FLinearColor(0.035601f, 0.035601f, 0.035601f)))
			.SetPressed(BOX_BRUSH("Common/FlatButton", 2.0f / 8.0f, FLinearColor(0.066626f, 0.066626f, 0.066626f)))
			.SetNormalPadding(FMargin(2, 2, 2, 2))
			.SetPressedPadding(FMargin(2, 3, 2, 1))
			.SetNormalForeground(FLinearColor::White)
			.SetPressedForeground(FLinearColor::White)
			.SetHoveredForeground(FLinearColor::White)
			.SetDisabledForeground(FLinearColor::White));

#undef BOX_BRUSH

		///////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////

		FSlateStyleRegistry::RegisterSlateStyle(*GVoxelPluginInstallerStyle);

		GVoxelPluginApi = new FVoxelPluginApi();
		GVoxelAuthDownload = new FVoxelPluginDownload();

		UToolMenu* ToolBar = UToolMenus::Get()->RegisterMenu(
			"LevelEditor.LevelEditorToolBar.AssetsToolBar",
			NAME_None,
			EMultiBoxType::SlimHorizontalToolBar,
			false);

		FToolMenuSection& Section = ToolBar->FindOrAddSection("ProjectSettings");

		FVoxelInstallerUtilities::DelayedCall([]
		{
			GVoxelPluginApi->Initialize();

			if (FParse::Param(FCommandLine::Get(), TEXT("ShowVoxelExamples")))
			{
				if (IVoxelEditorModule* EditorModule = FVoxelInstallerUtilities::GetEditorModule())
				{
					EditorModule->ShowContent();
				}
			}
		});

		Section.AddDynamicEntry("VoxelPluginMenu", FNewToolMenuSectionDelegate::CreateLambda([](FToolMenuSection& InSection)
		{
			InSection.AddEntry(FToolMenuEntry::InitComboButton(
				"Voxel",
				FUIAction(),
				FOnGetContent::CreateLambda([]
				{
					return SNew(SVoxelPluginWidget);
				}),
				INVTEXT("Voxel"),
				INVTEXT("Voxel Plugin configuration"),
				MakeAttributeLambda([]
				{
					if (GVoxelPluginApi->GetPluginState() == FVoxelPluginApi::EState::HasUpdate)
					{
						return FSlateIcon("VoxelPluginInstallerStyle", "VoxelIconWithUpdate");
					}
					else
					{
						return FSlateIcon("VoxelPluginInstallerStyle", "VoxelIcon");
					}
				})
			));
		}));
	}
};

IMPLEMENT_MODULE(FVoxelPluginInstallerModule, VoxelPluginInstaller);