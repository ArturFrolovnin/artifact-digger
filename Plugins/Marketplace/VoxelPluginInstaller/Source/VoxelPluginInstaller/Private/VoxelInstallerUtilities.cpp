// Copyright Voxel Plugin SAS. All Rights Reserved.

#include "VoxelInstallerUtilities.h"
#include "VoxelPluginApi.h"

#include "Misc/ScopeExit.h"
#include "Containers/Ticker.h"
#include "Interfaces/IPluginManager.h"

// Hack to make the marketplace review happy
#include "miniz.h"
#include "miniz.cpp"

DEFINE_LOG_CATEGORY(LogVoxelInstaller);

void FVoxelInstallerUtilities::DelayedCall(TFunction<void()> Call, float Delay)
{
	check(IsInGameThread());

	FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([=](float)
	{
		Call();
		return false;
	}), Delay);
}

FString FVoxelInstallerUtilities::Unzip(const TArray64<uint8>& Data, TMap<FString, TArray64<uint8>>& OutFiles)
{
#define CheckZip(...) \
		if ((__VA_ARGS__) != MZ_TRUE) \
		{ \
			return FString(mz_zip_get_error_string(mz_zip_peek_last_error(&Zip))); \
		} \
		{ \
			const mz_zip_error Error = mz_zip_peek_last_error(&Zip); \
			if (Error != MZ_ZIP_NO_ERROR) \
			{ \
				return FString(mz_zip_get_error_string(Error)); \
			} \
		}

#define CheckZipError() CheckZip(MZ_TRUE)

	mz_zip_archive Zip;
	mz_zip_zero_struct(&Zip);
	ON_SCOPE_EXIT
	{
		mz_zip_end(&Zip);
	};

	CheckZip(mz_zip_reader_init_mem(&Zip, Data.GetData(), Data.Num(), 0));

	const int32 NumFiles = mz_zip_reader_get_num_files(&Zip);

	for (int32 FileIndex = 0; FileIndex < NumFiles; FileIndex++)
	{
		const int32 FilenameSize = mz_zip_reader_get_filename(&Zip, FileIndex, nullptr, 0);
		CheckZipError();

		TArray64<char> FilenameBuffer;
		FilenameBuffer.SetNumUninitialized(FilenameSize);
		mz_zip_reader_get_filename(&Zip, FileIndex, FilenameBuffer.GetData(), FilenameBuffer.Num());
		CheckZipError();

		// To be extra safe
		FilenameBuffer.Add(0);

		const FString Filename = FString(FilenameBuffer.GetData());
		if (Filename.EndsWith("/"))
		{
			continue;
		}

		mz_zip_archive_file_stat FileStat;
		CheckZip(mz_zip_reader_file_stat(&Zip, FileIndex, &FileStat));

		TArray64<uint8> Buffer;
		Buffer.SetNumUninitialized(FileStat.m_uncomp_size);

		CheckZip(mz_zip_reader_extract_file_to_mem(&Zip, FilenameBuffer.GetData(), Buffer.GetData(), Buffer.Num(), 0));

		ensure(!OutFiles.Contains(Filename));
		OutFiles.Add(Filename, MoveTemp(Buffer));
	}

	return {};

#undef CheckZipError
#undef CheckZip
}

IVoxelEditorModule* FVoxelInstallerUtilities::GetEditorModule()
{
	FName ModuleName = "VoxelEditor";
	if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("Voxel"))
	{
		for (const FModuleDescriptor& Module : Plugin->GetDescriptor().Modules)
		{
			if (Module.Name == "VoxelContentEditor")
			{
				ModuleName = Module.Name;
				break;
			}
		}
	}

	return FModuleManager::Get().LoadModulePtr<IVoxelEditorModule>(ModuleName);
}