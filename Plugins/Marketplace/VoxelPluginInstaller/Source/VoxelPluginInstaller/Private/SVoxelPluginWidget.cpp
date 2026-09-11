// Copyright Voxel Plugin SAS. All Rights Reserved.

#include "SVoxelPluginWidget.h"

#include "VoxelPluginDownload.h"
#include "VoxelInstallerSettings.h"
#include "VoxelInstallerUtilities.h"
#include "SVoxelPluginSectionWidget.h"

#include "EditorFontGlyphs.h"
#include "ScopedTransaction.h"
#include "GameProjectGenerationModule.h"
#include "ISettingsEditorModule.h"
#include "SSearchableComboBox.h"
#include "HAL/FileManager.h"
#include "Interfaces/IProjectManager.h"
#include "Misc/MessageDialog.h"
#include "Styling/SlateStyle.h"
#include "Styling/StyleColors.h"
#include "Widgets/Images/SThrobber.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SWidgetSwitcher.h"

extern FSlateStyleSet* GVoxelPluginInstallerStyle;
static TOptional<TSharedPtr<IPlugin>> EnabledPluginOverride;

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

class SVoxelPluginInfoListRow : public SMultiColumnTableRow<TSharedPtr<FVoxelPluginApi::FPluginInfo>>
{
public:
	SLATE_BEGIN_ARGS(SVoxelPluginInfoListRow) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, const TSharedRef<STableViewBase>& InOwnerTableView, const TSharedPtr<FVoxelPluginApi::FPluginInfo>& InPluginInfo)
	{
		PluginInfo = InPluginInfo;
		SMultiColumnTableRow<TSharedPtr<FVoxelPluginApi::FPluginInfo>>::Construct(FSuperRowType::FArguments(), InOwnerTableView);
	}

	virtual TSharedRef<SWidget> GenerateWidgetForColumn(const FName& ColumnName) override
	{
		const auto IsPluginEnabled = [this]
		{
			if (EnabledPluginOverride)
			{
				return EnabledPluginOverride == PluginInfo->Plugin;
			}
			else
			{
				return PluginInfo->Plugin->IsEnabled();
			}
		};

		if (ColumnName == "Version")
		{
			return
				SNew(SBox)
				.Padding(8.f, 0.f, 0.f, 0.f)
				[
					SNew(STextBlock)
					.Text(FText::FromString(PluginInfo->GetVersionDisplayString()))
				];
		}

		if (ColumnName == "Location")
		{
			return
				SNew(STextBlock)
				.Text_Lambda([this]
				{
					if (*PluginInfo->IsDeleted)
					{
						return INVTEXT("Deleted");
					}

					return
						PluginInfo->Plugin->GetLoadedFrom() == EPluginLoadedFrom::Engine
						? INVTEXT("Engine Plugin")
						: INVTEXT("Project Plugin");
				});
		}

		if (ColumnName == "Actions")
		{
			return
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(3.f, 0.f)
				.VAlign(VAlign_Center)
				.HAlign(HAlign_Center)
				[
					SNew(SCheckBox)
					.IsEnabled_Lambda([this]
					{
						return !*PluginInfo->IsDeleted;
					})
					.ToolTipText_Lambda([IsPluginEnabled]
					{
						return IsPluginEnabled()
							? INVTEXT("Disable this plugin")
							: INVTEXT("Enable this plugin");
					})
					.IsChecked_Lambda([IsPluginEnabled]
					{
						return IsPluginEnabled() ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
					})
					.OnCheckStateChanged_Lambda([this](const ECheckBoxState NewState)
					{
						for (const FVoxelPluginApi::FPluginInfo& OtherPluginInfo : GVoxelPluginApi->GetInstalledPlugins())
						{
							FText FailMessage;
							if (!IProjectManager::Get().SetPluginEnabled(OtherPluginInfo.Plugin->GetName(), false, FailMessage))
							{
								FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
								return;
							}
						}

						if (NewState == ECheckBoxState::Unchecked)
						{
							EnabledPluginOverride = nullptr;
						}
						else
						{
							FText FailMessage;
							if (!IProjectManager::Get().SetPluginEnabled(PluginInfo->Plugin->GetName(), true, FailMessage))
							{
								FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
							}

							EnabledPluginOverride = PluginInfo->Plugin;
						}

						if (IProjectManager::Get().IsCurrentProjectDirty())
						{
							FGameProjectGenerationModule::Get().TryMakeProjectFileWriteable(FPaths::GetProjectFilePath());

							FText FailMessage;
							if (!IProjectManager::Get().SaveCurrentProjectToDisk(FailMessage))
							{
								FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
							}
						}

						FModuleManager::GetModuleChecked<ISettingsEditorModule>("SettingsEditor").OnApplicationRestartRequired();
					})
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(3.f, 0.f)
				.VAlign(VAlign_Center)
				.HAlign(HAlign_Center)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), TEXT("SimpleButton"))
					.OnClicked_Lambda([this]
					{
						const FString Path = FPaths::ConvertRelativePathToFull(PluginInfo->Plugin->GetBaseDir());
						UE_LOG(LogVoxelInstaller, Log, TEXT("Deleting %s"), *Path);

						if (!IFileManager::Get().DeleteDirectory(*Path, true, true))
						{
							FMessageDialog::Open(EAppMsgType::Ok, FText::Format(INVTEXT("Failed to delete {0}"), FText::FromString(Path)));
						}

						*PluginInfo->IsDeleted = true;

						return FReply::Handled();
					})
					.IsEnabled_Lambda([this, IsPluginEnabled]
					{
						return
							!IsPluginEnabled() &&
							!PluginInfo->Plugin->IsEnabled() &&
							!*PluginInfo->IsDeleted;
					})
					.ToolTipText_Lambda([this]
					{
						if (IsEnabled())
						{
							return INVTEXT("Cannot delete enabled plugins");
						}
						if (PluginInfo->Plugin->IsEnabled())
						{
							return INVTEXT("Please restart the engine to delete this plugin");
						}
						if (*PluginInfo->IsDeleted)
						{
							return INVTEXT("Already deleted");
						}
						return INVTEXT("Delete this plugin");
					})
					.ContentPadding(FMargin(0))
					[
						SNew(STextBlock)
						.Font(FAppStyle::Get().GetFontStyle("FontAwesome.14"))
						.Text(FEditorFontGlyphs::Trash)
					]
				];
		}

		ensure(false);
		return SNullWidget::NullWidget;
	}

private:
	TSharedPtr<FVoxelPluginApi::FPluginInfo> PluginInfo;
};

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void SVoxelPluginWidget::Construct(const FArguments& Args)
{
	GVoxelPluginApi->RefreshUser();
	GVoxelPluginApi->UpdateVersions();

	ChildSlot
	[
		SNew(SBox)
		.MinDesiredWidth(300.f)
		.MinDesiredHeight(350.f)
		.Padding(1.f)
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SNew(SBox)
				.IsEnabled_Lambda([]
				{
					return GVoxelPluginApi->IsConfigReady();
				})
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(10.f)
					[
						MakeHeaderSection()
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						MakeUserSection()
					]
					+ SVerticalBox::Slot()
					.FillHeight(1.f)
					[
						MakeInstalledVersionsSection()
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						MakeInstallPluginSection()
					]
				]
			]
			+ SOverlay::Slot()
			[
				SNew(SBox)
				.Visibility_Lambda([]
				{
					return GVoxelPluginApi->IsConfigReady() ? EVisibility::Collapsed : EVisibility::Visible;
				})
				.VAlign(VAlign_Center)
				.HAlign(HAlign_Center)
				[
					SNew(SThrobber)
				]
			]
		]
	];
}

TSharedRef<SWidget> SVoxelPluginWidget::MakeHeaderSection()
{
	return
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		[
			SNew(SButton)
			.Visibility_Lambda([]
			{
				return GVoxelPluginApi->GetConfig().bShowLoginButton ? EVisibility::Visible : EVisibility::Collapsed;
			})
			.IsEnabled_Lambda([]
			{
				return !GVoxelPluginApi->IsRefreshingUser();
			})
			.ToolTipText_Lambda([]
			{
				return GVoxelPluginApi->IsLoggedIn() ? INVTEXT("Logout") : INVTEXT("Login");
			})
			.OnClicked_Lambda([]
			{
				if (GVoxelPluginApi->IsLoggedIn())
				{
					if (FMessageDialog::Open(EAppMsgType::YesNoCancel, INVTEXT("Do you want to log out?")) == EAppReturnType::Yes)
					{
						GVoxelPluginApi->Logout();
					}

					return FReply::Handled();
				}
				else
				{
					GVoxelPluginApi->Login();
					return FReply::Handled();
				}
			})
			.ButtonStyle(GVoxelPluginInstallerStyle, "EpicButton")
			.ContentPadding(FMargin(7.f, 0.f))
			[
				SNew(SBox)
				.WidthOverride(80.f)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SWidgetSwitcher)
					.WidgetIndex_Lambda([]
					{
						return GVoxelPluginApi->IsRefreshingUser() ? 0 : 1;
					})
					+ SWidgetSwitcher::Slot()
					[
						SNew(SThrobber)
					]
					+ SWidgetSwitcher::Slot()
					[
						SNew(STextBlock)
						.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
						.Text_Lambda([]
						{
							return GVoxelPluginApi->IsLoggedIn() ? INVTEXT("Logout") : INVTEXT("Login");
						})
					]
				]
			]
		]
		+ SHorizontalBox::Slot()
		.FillWidth(1.f)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(2.5f, 0.f)
		[
			MakeURLIconButton("Open documentation", "https://docs.voxelplugin.com", FAppStyle::Get().GetBrush("Icons.Documentation"))
		]
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(2.5f, 0.f)
		[
			MakeURLIconButton("Open contact email", "mailto:contact@voxelplugin.com", GVoxelPluginInstallerStyle->GetBrush("EmailIcon"))
		]
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(2.5f, 0.f)
		[
			MakeURLIconButton("Open discord", "https://discord.voxelplugin.com", GVoxelPluginInstallerStyle->GetBrush("DiscordIcon"))
		];
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

TSharedRef<SWidget> SVoxelPluginWidget::MakeUserSection()
{
	return
		SNew(SVoxelPluginSectionWidget)
		.Visibility_Lambda([]
		{
			return GVoxelPluginApi->IsLoggedIn() ? EVisibility::Visible : EVisibility::Collapsed;
		})
		.Title(INVTEXT("User"))
		.ContentPadding(FMargin(10.f, 0.f, 10.f, 10.f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.Padding(0.f, 5.f)
			.AutoHeight()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(STextBlock)
					.Text(INVTEXT("Logged in as: "))
					.ColorAndOpacity(FSlateColor::UseForeground())
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(STextBlock)
					.Text_Lambda([]
					{
						return FText::FromString(GVoxelPluginApi->GetUser().Email);
					})
					.ColorAndOpacity(FStyleColors::ForegroundHover)
				]
			]
			+ SVerticalBox::Slot()
			.Padding(0.f, 5.f)
			.AutoHeight()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(STextBlock)
					.Text(INVTEXT("License state: "))
					.ColorAndOpacity(FSlateColor::UseForeground())
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(STextBlock)
					.Text_Lambda([]
					{
						return GVoxelPluginApi->GetUser().bHasValidLicense ? INVTEXT("Active") : INVTEXT("No active license");
					})
					.ColorAndOpacity_Lambda([]
					{
						return GVoxelPluginApi->GetUser().bHasValidLicense ? FStyleColors::AccentGreen : FStyleColors::Warning;
					})
				]
			]
			+ SVerticalBox::Slot()
			.Padding(0.f, 5.f, 0.f, 0.f)
			.HAlign(HAlign_Center)
			[
				SNew(SButton)
	            .OnClicked_Lambda([=]
	            {
	                FPlatformProcess::LaunchURL(TEXT("https://new.voxelplugin.com/vault"), nullptr, nullptr);
	                return FReply::Handled();
	            })
	            .ContentPadding(FMargin(0.f, 5.f, 0.f, 4.f))
	            [
	                SNew(SHorizontalBox)
	                + SHorizontalBox::Slot()
	                .HAlign(HAlign_Center)
	                .VAlign(VAlign_Center)
	                [
                		SNew(SImage)
                		.Image(GVoxelPluginInstallerStyle->GetBrush("AccountIcon"))
                		.ColorAndOpacity(FStyleColors::AccentGreen)
	                ]
	                + SHorizontalBox::Slot()
	                .Padding(5.f, 0.f, 0.f, 0.f)
	                .VAlign(VAlign_Center)
	                .AutoWidth()
	                [
                		SNew(STextBlock)
                		.TextStyle(FAppStyle::Get(), "SmallButtonText")
                		.Text(INVTEXT("Manage Licenses"))
	                ]
	            ]
			]
		];
}

TSharedRef<SWidget> SVoxelPluginWidget::MakeInstalledVersionsSection()
{
	IVoxelEditorModule* EditorModule = FVoxelInstallerUtilities::GetEditorModule();

	for (const FVoxelPluginApi::FPluginInfo& PluginInfo : GVoxelPluginApi->GetInstalledPlugins())
	{
		InstalledPlugins.Add(MakeShared<FVoxelPluginApi::FPluginInfo>(PluginInfo));
	}

	return
		SNew(SVoxelPluginSectionWidget)
		.Title(INVTEXT("Installed Versions"))
		.ContentPadding(FMargin(0.f, 10.f, 0.f, 0.f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.FillHeight(1.f)
			[
				SNew(SBox)
				.HeightOverride(100.f)
				[
					SNew(SOverlay)
					+ SOverlay::Slot()
					[
						SNew(SListView<TSharedPtr<FVoxelPluginApi::FPluginInfo>>)
						.ListItemsSource(&InstalledPlugins)
						.HeaderRow(
							SNew(SHeaderRow)
							+ SHeaderRow::Column("Version")
							.HeaderContentPadding(FMargin(8.f, 0.f, 0.f, 0.f))
							.DefaultLabel(INVTEXT("Version"))
							.FillWidth(0.4f)
							.VAlignCell(VAlign_Center)
							+ SHeaderRow::Column("Location")
							.DefaultLabel(INVTEXT("Location"))
							.FillWidth(0.35f)
							.VAlignCell(VAlign_Center)
							+ SHeaderRow::Column("Actions")
							.DefaultLabel(INVTEXT(""))
							.FillWidth(0.25f)
							.HAlignHeader(HAlign_Center)
							.HAlignCell(HAlign_Center)
							.VAlignCell(VAlign_Center)
						)
						.OnGenerateRow_Lambda([this](TSharedPtr<FVoxelPluginApi::FPluginInfo> PluginInfo, const TSharedRef<STableViewBase>& Owner)
						{
							return SNew(SVoxelPluginInfoListRow, Owner, PluginInfo);
						})
					]
					+ SOverlay::Slot()
					.VAlign(VAlign_Center)
					.HAlign(HAlign_Center)
					[
						SNew(STextBlock)
						.Visibility_Lambda([]
						{
							return GVoxelPluginApi->GetInstalledPlugins().Num() == 0 ? EVisibility::Visible : EVisibility::Collapsed;
						})
						.Text(INVTEXT("Currently no version installed"))
					]
				]
			]
			+ SVerticalBox::Slot()
			.VAlign(VAlign_Center)
			.HAlign(HAlign_Center)
			.AutoHeight()
			.Padding(0.f, 4.f)
			[
				SNew(SButton)
				.Visibility_Lambda([=]
				{
					return EditorModule ? EVisibility::Visible : EVisibility::Collapsed;
				})
				.OnClicked_Lambda([=]
				{
					EditorModule->ShowContent();
					return FReply::Handled();
				})
				.ContentPadding(FMargin(0, 5.f, 0, 4.f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					[
						SNew(SImage)
						.Image(FAppStyle::Get().GetBrush("MainFrame.VisitOnlineLearning"))
						.ColorAndOpacity(FStyleColors::White)
					]
					+ SHorizontalBox::Slot()
					.Padding(FMargin(5, 0, 0, 0))
					.VAlign(VAlign_Center)
					.AutoWidth()
					[
						SNew(STextBlock)
						.TextStyle(FAppStyle::Get(), "SmallButtonText")
						.Text(INVTEXT("Open Plugin Examples"))
					]
				]
			]
		];
}

TSharedRef<SWidget> SVoxelPluginWidget::MakeInstallPluginSection()
{
	AvailablePluginVersions = {};
	for (const TSharedPtr<FVoxelPluginVersion>& Version : GVoxelPluginApi->AllVersions)
	{
		AvailablePluginVersions.Add(MakeShared<FString>(Version->ToString_API()));
	}

	const TSharedPtr<SSearchableComboBox> VersionComboBox =
		SNew(SSearchableComboBox)
		.IsEnabled_Lambda([]
		{
			return GVoxelPluginApi->AllVersions.Num() > 0;
		})
		.OptionsSource(&AvailablePluginVersions)
		.OnGenerateWidget_Lambda([](const TSharedPtr<FString>& Item) -> TSharedRef<SWidget>
		{
			if (!ensure(Item))
			{
				return SNullWidget::NullWidget;
			}

			if (const TSharedPtr<FVoxelPluginVersion> PluginVersion = GVoxelPluginApi->VersionStringToVersion.FindRef(*Item))
			{
				return
					SNew(STextBlock)
					.Text(FText::FromString(PluginVersion->ToString_UserFacing()));
			}

			return SNullWidget::NullWidget;
		})
		.OnSelectionChanged_Lambda([](const TSharedPtr<FString>& Item, ESelectInfo::Type)
		{
			if (!ensure(Item))
			{
				return;
			}

			if (const TSharedPtr<FVoxelPluginVersion> PluginVersion = GVoxelPluginApi->VersionStringToVersion.FindRef(*Item))
			{
				GVoxelPluginApi->SelectedVersion = *PluginVersion;
			}
		})
		[
			SNew(STextBlock)
			.Text_Lambda([]
			{
				if (GVoxelPluginApi->IsUpdatingVersions())
				{
					return INVTEXT("Loading...");
				}

				if (GVoxelPluginApi->AllVersions.Num() == 0)
				{
					return INVTEXT("---");
				}

				return FText::FromString(GVoxelPluginApi->SelectedVersion.ToString_UserFacing());
			})
		];

	GVoxelPluginApi->OnComboBoxesUpdated.AddSPLambda(this, [WeakThis = TWeakPtr<SVoxelPluginWidget>(SharedThis(this)), WeakComboBox = TWeakPtr<SSearchableComboBox>(VersionComboBox)]
	{
		const TSharedPtr<SVoxelPluginWidget> This = WeakThis.Pin();
		if (!This)
		{
			return;
		}

		This->AvailablePluginVersions = {};
		for (const TSharedPtr<FVoxelPluginVersion>& Version : GVoxelPluginApi->AllVersions)
		{
			This->AvailablePluginVersions.Add(MakeShared<FString>(Version->ToString_API()));
		}

		if (const TSharedPtr<SSearchableComboBox> ComboBox = WeakComboBox.Pin())
		{
			ComboBox->RefreshOptions();
		}
	});

	return
		SNew(SVoxelPluginSectionWidget)
		.Visibility_Lambda([]
		{
			return
				GVoxelPluginApi->IsLoggedIn() &&
				GVoxelPluginApi->GetUser().bHasValidLicense
				? EVisibility::Visible
				: EVisibility::Collapsed;
		})
		.Title(INVTEXT("Install"))
		.ContentPadding(FMargin(10.f, 5.f, 10.f, 10.f))
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SNew(SGridPanel)
				.IsEnabled_Lambda([]
				{
					return !GVoxelPluginApi->IsUpdatingVersions();
				})
				.FillColumn(0, 0.6f)
				.FillColumn(1, 0.4f)
				+ SGridPanel::Slot(0, 0)
				.Padding(0.f, 2.5f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(INVTEXT("Version to install:"))
				]
				+ SGridPanel::Slot(1, 0)
				.VAlign(VAlign_Center)
				[
					VersionComboBox.ToSharedRef()
				]
				+ SGridPanel::Slot(0, 1)
				.Padding(0.f, 2.5f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(INVTEXT("Install in engine"))
				]
				+ SGridPanel::Slot(1, 1)
				.Padding(0.f, 5.f)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SCheckBox)
					.IsEnabled_Lambda([]
					{
						return GVoxelPluginApi->AllVersions.Num() > 0;
					})
					.IsChecked_Lambda([]
					{
						return GetDefault<UVoxelInstallerSettings>()->bInstallInEngine ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
					})
					.OnCheckStateChanged_Lambda([](const ECheckBoxState NewState)
					{
						UVoxelInstallerSettings* Settings = GetMutableDefault<UVoxelInstallerSettings>();

						FScopedTransaction Transaction(TEXT("Set Install in Engine"), INVTEXT("Set Install in Engine"), Settings);
						Settings->Modify();
						Settings->bInstallInEngine = NewState == ECheckBoxState::Checked;
						Settings->PostEditChange();
						Settings->TryUpdateDefaultConfigFile();
					})
				]
				+ SGridPanel::Slot(0, 2)
				.Padding(0.f, 2.5f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(INVTEXT("Show Dev Versions"))
				]
				+ SGridPanel::Slot(1, 2)
				.Padding(0.f, 5.f)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SCheckBox)
					.IsChecked_Lambda([]
					{
						return GetDefault<UVoxelInstallerSettings>()->bShowDevVersions ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
					})
					.OnCheckStateChanged_Lambda([](const ECheckBoxState NewState)
					{
						UVoxelInstallerSettings* Settings = GetMutableDefault<UVoxelInstallerSettings>();

						{
							FScopedTransaction Transaction(TEXT("Set Show Dev Versions"), INVTEXT("Set Show Dev Versions"), Settings);
							Settings->Modify();
							Settings->bShowDevVersions = NewState == ECheckBoxState::Checked;
							Settings->PostEditChange();
							Settings->TryUpdateDefaultConfigFile();
						}

						GVoxelPluginApi->RefreshUser();
						GVoxelPluginApi->UpdateVersions();
					})
				]
				+ SGridPanel::Slot(0, 3)
				.Padding(0.f, 2.5f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(INVTEXT("Show Unstable Versions"))
					.Visibility_Lambda([]
					{
						return GetDefault<UVoxelInstallerSettings>()->bShowDevVersions ? EVisibility::Visible : EVisibility::Collapsed;
					})
				]
				+ SGridPanel::Slot(1, 3)
				.Padding(0.f, 5.f)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SCheckBox)
					.IsChecked_Lambda([]
					{
						return GetDefault<UVoxelInstallerSettings>()->bShowUnstableVersions ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
					})
					.OnCheckStateChanged_Lambda([](const ECheckBoxState NewState)
					{
						UVoxelInstallerSettings* Settings = GetMutableDefault<UVoxelInstallerSettings>();

						{
							FScopedTransaction Transaction(TEXT("Set Show Unstable Versions"), INVTEXT("Set Show Unstable Versions"), Settings);
							Settings->Modify();
							Settings->bShowUnstableVersions = NewState == ECheckBoxState::Checked;
							Settings->PostEditChange();
							Settings->TryUpdateDefaultConfigFile();
						}

						GVoxelPluginApi->RefreshUser();
						GVoxelPluginApi->UpdateVersions();
					})
					.Visibility_Lambda([]
					{
						return GetDefault<UVoxelInstallerSettings>()->bShowDevVersions ? EVisibility::Visible : EVisibility::Collapsed;
					})
				]
				+ SGridPanel::Slot(1, 4)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SButton)
					.IsEnabled_Lambda([]
					{
						return GVoxelPluginApi->AllVersions.Num() > 0;
					})
					.OnClicked_Lambda([=]
					{
						GVoxelAuthDownload->Download(
							GVoxelPluginApi->SelectedVersion,
							GetDefault<UVoxelInstallerSettings>()->bInstallInEngine);
						return FReply::Handled();
					})
					.ContentPadding(FMargin(0, 5.f, 0, 4.f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot()
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(SImage)
							.Image(FAppStyle::Get().GetBrush("Icons.CircleArrowDown"))
							.ColorAndOpacity(FStyleColors::AccentGreen)
						]
						+ SHorizontalBox::Slot()
						.Padding(FMargin(5, 0, 0, 0))
						.VAlign(VAlign_Center)
						.AutoWidth()
						[
							SNew(STextBlock)
							.TextStyle(FAppStyle::Get(), "SmallButtonText")
							.Text(INVTEXT("Install"))
						]
					]
				]
				+ SGridPanel::Slot(0, 5)
				.ColumnSpan(2)
				.Padding(0.f, 2.5f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Justification(ETextJustify::Center)
					.Visibility_Lambda([]
					{
						return
							!GVoxelPluginApi->IsUpdatingVersions() &&
							GVoxelPluginApi->AllVersions.Num() == 0
							? EVisibility::Visible
							: EVisibility::Collapsed;
					})
					.Text(INVTEXT("No available plugin for this engine version"))
					.ColorAndOpacity(FStyleColors::Warning)
					.AutoWrapText(true)
				]
			]
			+ SOverlay::Slot()
			.VAlign(VAlign_Center)
			.HAlign(HAlign_Center)
			[
				SNew(SThrobber)
				.Visibility_Lambda([]
				{
					return GVoxelPluginApi->IsUpdatingVersions() ? EVisibility::Visible : EVisibility::Collapsed;
				})
			]
		];
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

TSharedRef<SButton> SVoxelPluginWidget::MakeLoginButton()
{
	return
		SNew(SButton)
		.Visibility_Lambda([]
		{
			return GVoxelPluginApi->GetConfig().bShowLoginButton ? EVisibility::Visible : EVisibility::Collapsed;
		})
		.ToolTipText_Lambda([]
		{
			if (GVoxelPluginApi->IsLoggedIn())
			{
				return INVTEXT("Logout");
			}
			else
			{
				return INVTEXT("Login");
			}
		})
		.OnClicked_Lambda([]
		{
			if (GVoxelPluginApi->IsLoggedIn())
			{
				if (FMessageDialog::Open(EAppMsgType::YesNoCancel, INVTEXT("Do you want to log out?")) == EAppReturnType::Yes)
				{
					GVoxelPluginApi->Logout();
				}
				return FReply::Handled();
			}
			else
			{
				GVoxelPluginApi->Login();
				return FReply::Handled();
			}
		})
		.ButtonStyle(GVoxelPluginInstallerStyle, "EpicButton")
		.ContentPadding(FMargin(7.f, 0.f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(SWidgetSwitcher)
			.WidgetIndex_Lambda([]
			{
				return GVoxelPluginApi->IsRefreshingUser() ? 0 : 1;
			})
			+ SWidgetSwitcher::Slot()
			[
				SNew(SThrobber)
			]
			+ SWidgetSwitcher::Slot()
			[
				SNew(STextBlock)
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
				.Text_Lambda([]
				{
					return GVoxelPluginApi->IsLoggedIn() ? INVTEXT("Logout") : INVTEXT("Login");
				})
			]
		];
}

TSharedRef<SButton> SVoxelPluginWidget::MakeURLIconButton(const FString& ToolTip, const FString& URL, const FSlateBrush* Icon)
{
	return
		SNew(SButton)
		.ToolTipText(FText::FromString(ToolTip))
		.OnClicked_Lambda([=]
		{
			FPlatformProcess::LaunchURL(*URL, nullptr, nullptr);
			return FReply::Handled();
		})
		.ButtonStyle(FAppStyle::Get(), "HoverHintOnly")
		[
			SNew(SBox)
			.WidthOverride(20)
			.HeightOverride(20)
			[
				SNew(SScaleBox)
				.Stretch(EStretch::ScaleToFit)
				[
					SNew(SImage)
					.Image(Icon)
				]
			]
		];
}