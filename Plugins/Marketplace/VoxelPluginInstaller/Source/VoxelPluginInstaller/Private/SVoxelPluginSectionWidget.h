// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SHeader.h"
#include "Widgets/Layout/SSeparator.h"

class SVoxelPluginSectionWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SVoxelPluginSectionWidget) {}
		SLATE_ARGUMENT(FText, Title)
		SLATE_ARGUMENT(FMargin, ContentPadding)
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		ChildSlot
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f)
			[
				SNew(SSeparator)
			]
			+ SVerticalBox::Slot()
			.FillHeight(1.f)
			.Padding(0.f)
			[
				SNew(SBorder)
				.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
				.Padding(0.f, 10.f, 0.f, 0.f)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(10.f, 0.f)
					[
						SNew(SHeader)
						[
							SNew(STextBlock)
							.Text(InArgs._Title)
							.TextStyle(FAppStyle::Get(), "LargeText")
							.ColorAndOpacity(FSlateColor::UseForeground())
						]
					]
					+ SVerticalBox::Slot()
					.FillHeight(1.f)
					.Padding(InArgs._ContentPadding)
					.HAlign(HAlign_Fill)
					.VAlign(VAlign_Fill)
					[
						InArgs._Content.Widget
					]
				]
			]
		];
	}
};