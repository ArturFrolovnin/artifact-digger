// Copyright Voxel Plugin SAS. All Rights Reserved.

#include "VoxelPluginDownload.h"
#include "VoxelPluginApi.h"
#include "VoxelInstallerSettings.h"
#include "VoxelInstallerUtilities.h"
#include "HttpModule.h"
#include "Misc/Base64.h"
#include "Misc/FileHelper.h"
#include "Misc/CommandLine.h"
#include "Misc/MessageDialog.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "ISourceControlModule.h"
#include "ISourceControlProvider.h"
#include "SourceControlOperations.h"
#include "Serialization/JsonReader.h"
#include "Interfaces/IHttpResponse.h"
#include "Interfaces/IPluginManager.h"
#include "Interfaces/IProjectManager.h"
#include "GameProjectGenerationModule.h"
#include "Serialization/JsonSerializer.h"
#include "Compression/OodleDataCompressionUtil.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Framework/Notifications/NotificationManager.h"
#if PLATFORM_MAC
#include <sys/stat.h>
#endif

FVoxelPluginDownload* GVoxelAuthDownload = nullptr;

void FVoxelPluginDownload::Download(
	const FVoxelPluginVersion& Version,
	const bool bInstallInEngine)
{
	if (!Version.bNoSource)
	{
		GVoxelPluginApi->RefreshUser();

		if (!GVoxelPluginApi->IsLoggedIn() &&
			GVoxelPluginApi->IsRefreshingUser())
		{
			FNotificationInfo Info(INVTEXT("Logging in"));
			Info.bFireAndForget = false;
			Info.ExpireDuration = 0.f;
			Info.FadeInDuration = 0.f;
			Info.FadeOutDuration = 0.f;
			Info.WidthOverride = FOptionalSize();

			const TSharedPtr<SNotificationItem> LoginNotification = FSlateNotificationManager::Get().AddNotification(Info);
			LoginNotification->SetCompletionState(SNotificationItem::CS_Pending);

			FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([=, this](float)
			{
				if (GVoxelPluginApi->IsLoggedIn())
				{
					LoginNotification->ExpireAndFadeout();
					Download(Version, bInstallInEngine);
					return false;
				}

				if (GVoxelPluginApi->IsRefreshingUser())
				{
					return true;
				}

				LoginNotification->ExpireAndFadeout();
				FMessageDialog::Open(EAppMsgType::Ok, FText::FromString("Cannot download Voxel Plugin update: please login again from the Voxel menu top right of the editor"));
				return false;
			}));
			return;
		}

		if (!GVoxelPluginApi->IsLoggedIn())
		{
			FMessageDialog::Open(EAppMsgType::Ok, FText::FromString("Cannot download Voxel Plugin update: please login again from the Voxel menu top right of the editor"));
			return;
		}
	}

	if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("VoxelPro"))
	{
		const bool bIsError = [&]
		{
			if (Plugin->IsEnabled())
			{
				return true;
			}

			if (bInstallInEngine &&
				Plugin->GetLoadedFrom() == EPluginLoadedFrom::Engine)
			{
				return true;
			}

			if (!bInstallInEngine &&
				Plugin->GetLoadedFrom() == EPluginLoadedFrom::Project)
			{
				return true;
			}

			return false;
		}();

		if (bIsError)
		{
			FMessageDialog::Open(
				EAppMsgType::Ok,
				FText::FromString("VoxelPro found in " + FPaths::ConvertRelativePathToFull(Plugin->GetBaseDir()) + ". Please uninstall it first."));
			return;
		}
	}

	if (const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("VoxelFree"))
	{
		const bool bIsError = [&]
		{
			if (Plugin->IsEnabled())
			{
				return true;
			}

			if (bInstallInEngine &&
				Plugin->GetLoadedFrom() == EPluginLoadedFrom::Engine)
			{
				return true;
			}

			if (!bInstallInEngine &&
				Plugin->GetLoadedFrom() == EPluginLoadedFrom::Project)
			{
				return true;
			}

			return false;
		}();

		if (bIsError)
		{
			FMessageDialog::Open(
				EAppMsgType::Ok,
				FText::FromString("VoxelFree found in " + FPaths::ConvertRelativePathToFull(Plugin->GetBaseDir()) + ". Please uninstall it first."));
			return;
		}
	}

	if (bInstallInEngine)
	{
		for (const FVoxelPluginApi::FPluginInfo& PluginInfo : GVoxelPluginApi->GetInstalledPlugins())
		{
			if (PluginInfo.Plugin->GetLoadedFrom() != EPluginLoadedFrom::Engine ||
				*PluginInfo.IsDeleted)
			{
				continue;
			}

			if (!PluginInfo.bSourcePlugin &&
				Version == PluginInfo.Version)
			{
				continue;
			}

			if (EAppReturnType::Yes != FMessageDialog::Open(
				EAppMsgType::YesNoCancel,
				FText::FromString(
					"Installing version " +
					Version.ToString_UserFacing() +
					" will replace version " +
					PluginInfo.GetVersionDisplayString() +
					"\n\nPath: " + FPaths::ConvertRelativePathToFull(PluginInfo.Plugin->GetBaseDir()) +
					"\n\nDo you want to continue?")))
			{
				return;
			}
		}
	}
	else
	{
		for (const FVoxelPluginApi::FPluginInfo& PluginInfo : GVoxelPluginApi->GetInstalledPlugins())
		{
			if (PluginInfo.Plugin->GetLoadedFrom() != EPluginLoadedFrom::Project ||
				*PluginInfo.IsDeleted)
			{
				continue;
			}

			const FString ExpectedPath = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir() / "Voxel");

			const FString Path = FPaths::ConvertRelativePathToFull(PluginInfo.Plugin->GetBaseDir());
			if (!FPaths::IsSamePath(ExpectedPath, Path))
			{
				FMessageDialog::Open(
					EAppMsgType::Ok,
					FText::FromString("Voxel Plugin found in " + Path + ", but should be " + ExpectedPath + ". Please uninstall it or move it."));
				return;
			}

			if (!PluginInfo.bSourcePlugin &&
				Version == PluginInfo.Version)
			{
				continue;
			}

			if (EAppReturnType::Yes != FMessageDialog::Open(
				EAppMsgType::YesNoCancel,
				FText::FromString(
					"Installing version " +
					Version.ToString_UserFacing() +
					" will replace version " +
					PluginInfo.GetVersionDisplayString() +
					"\n\nPath: " + FPaths::ConvertRelativePathToFull(PluginInfo.Plugin->GetBaseDir()) +
					"\n\nDo you want to continue?")))
			{
				return;
			}
		}
	}

	if (Notification)
	{
		FMessageDialog::Open(EAppMsgType::Ok, INVTEXT("Already downloading. You might need to restart the engine."));
		return;
	}

	FNotificationInfo Info(FText::FromString("Downloading Voxel Plugin " + Version.ToString_UserFacing()));
	Info.bFireAndForget = false;
	Notification = FSlateNotificationManager::Get().AddNotification(Info);

	GVoxelPluginApi->MakeRequest(
		"version/download",
		{
			{ "version", Version.ToString_API() },
		},
		FVoxelPluginApi::ERequestVerb::Get,
		true,
		FHttpRequestCompleteDelegate::CreateLambda([=, this](
			const FHttpRequestPtr,
			const FHttpResponsePtr Response,
			const bool bConnectedSuccessfully)
		{
			if (!Response)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to get download URL: No response"));
				Fail("Failed get download URL for Voxel Plugin");
				return;
			}

			if (!bConnectedSuccessfully ||
				Response->GetResponseCode() != 200)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to get download URL: %d %s"), Response->GetResponseCode(), *Response->GetContentAsString());
				Fail("Failed get download URL for Voxel Plugin");
				return;
			}

			TSharedPtr<FJsonValue> ParsedValue;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
			if (!ensure(FJsonSerializer::Deserialize(Reader, ParsedValue)) ||
				!ensure(ParsedValue))
			{
				Fail("Failed parse response: " + Response->GetContentAsString());
				return;
			}

			const TSharedPtr<FJsonObject> Object = ParsedValue->AsObject();
			if (!ensure(Object))
			{
				Fail("Failed parse response: " + Response->GetContentAsString());
				return;
			}

			const FString Url = Object->GetStringField(TEXT("url"));
			const int64 Size = Object->GetNumberField(TEXT("size"));
			const FString Hash = Object->GetStringField(TEXT("hash"));
			const FString AesKey = Object->GetStringField(TEXT("aesKey"));
			if (!ensure(!Url.IsEmpty()) ||
				!ensure(Size > 0) ||
				!ensure(!Hash.IsEmpty()) ||
				!ensure(!AesKey.IsEmpty()))
			{
				Fail("Failed parse response: " + Response->GetContentAsString());
				return;
			}
			UE_LOG(LogVoxelInstaller, Log, TEXT("Hash: %s"), *Hash);

			const FString Path = GVoxelPluginApi->GetAppDataPath() / "Cache" / Hash;

			TArray<uint8> Result;
			if (FFileHelper::LoadFileToArray(Result, *Path))
			{
				if (ensure(FSHA1::HashBuffer(Result.GetData(), Result.Num()).ToString() == Hash))
				{
					IFileManager::Get().SetTimeStamp(*Path, FDateTime::UtcNow());
					FinalizeDownload(
						bInstallInEngine,
						Result,
						AesKey);
					return;
				}
			}

			const TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
			Request->SetURL(Url);
			Request->SetVerb(TEXT("GET"));
			Request->UE_504_SWITCH(OnRequestProgress, OnRequestProgress64)().BindLambda([=, this](FHttpRequestPtr, const UE_504_SWITCH(int32, int64) BytesSent, const UE_504_SWITCH(int32, int64) BytesReceived)
			{
				if (ensure(Notification))
				{
					Notification->SetSubText(FText::FromString(FString::Printf(
						TEXT("%.1f/%.1fMB"),
						BytesReceived / double(1 << 20),
						Size / double(1 << 20))));
				}
			});
			Request->OnProcessRequestComplete().BindLambda([
				this,
				Version,
				bInstallInEngine,
				Path,
				Hash,
				AesKey](FHttpRequestPtr, FHttpResponsePtr NewResponse, bool bNewConnectedSuccessfully)
			{
				if (!bNewConnectedSuccessfully ||
					!NewResponse ||
					NewResponse->GetResponseCode() != 200)
				{
					Fail("Failed to download Voxel Plugin");
					return;
				}

				const TArray<uint8>& Result = NewResponse->GetContent();

				if (!ensure(FSHA1::HashBuffer(Result.GetData(), Result.Num()).ToString() == Hash))
				{
					Fail("Failed to download Voxel Plugin: invalid hash");
					return;
				}

				ensure(FFileHelper::SaveArrayToFile(Result, *Path));
				IFileManager::Get().SetTimeStamp(*Path, FDateTime::UtcNow());

				for (int32 Loop = 0; Loop < 1000; Loop++)
				{
					TArray<FString> Files;
					IFileManager::Get().FindFilesRecursive(Files, *FPaths::GetPath(Path), TEXT("*"), true, false);

					int64 TotalSize = 0;
					for (const FString& File : Files)
					{
						TotalSize += IFileManager::Get().FileSize(*File);
					}

					const int64 MaxSize = FMath::Max<int64>(1, GetDefault<UVoxelInstallerSettings>()->CacheSizeInMB) * 1024 * 1024;
					if (TotalSize < MaxSize)
					{
						break;
					}

					FString OldestFile;
					FDateTime OldestFileTimestamp;
					for (const FString& File : Files)
					{
						const FDateTime Timestamp = IFileManager::Get().GetTimeStamp(*File);

						if (OldestFile.IsEmpty() ||
							Timestamp < OldestFileTimestamp)
						{
							OldestFile = File;
							OldestFileTimestamp = Timestamp;
						}
					}

					UE_LOG(LogVoxelInstaller, Log, TEXT("Deleting %s"), *OldestFile);
					ensure(IFileManager::Get().Delete(*OldestFile));
				}

				FinalizeDownload(
					bInstallInEngine,
					Result,
					AesKey);
			});
			Request->ProcessRequest();
		}));
}

void FVoxelPluginDownload::Fail(const FString& Error)
{
	FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Error));

	if (ensure(Notification))
	{
		Notification->ExpireAndFadeout();
		Notification.Reset();
	}
}

void FVoxelPluginDownload::FinalizeDownload(
	const bool bInstallInEngine,
	const TArray<uint8>& Data,
	const FString& AesKey)
{
	if (ensure(Notification))
	{
		Notification->SetText(INVTEXT("Decompressing Voxel Plugin"));
		Notification->SetSubText(INVTEXT(""));
	}

	FVoxelInstallerUtilities::DelayedCall([this, bInstallInEngine, Data = TArray64<uint8>(Data), AesKey]() mutable
	{
		FinalizeDownloadImpl(bInstallInEngine, MoveTemp(Data), AesKey);
	}, 0.5f);
}

void FVoxelPluginDownload::FinalizeDownloadImpl(
	const bool bInstallInEngine,
	TArray64<uint8> Data,
	const FString& AesKey)
{
	const FString InstallLocation =
		bInstallInEngine
		? FPaths::ConvertRelativePathToFull(FPaths::EnginePluginsDir() / "Marketplace" / "Voxel")
		: FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir() / "Voxel");

	UE_LOG(LogVoxelInstaller, Log, TEXT("Installing to %s"), *InstallLocation);

	TArray<uint8> AesKeyBits;
	if (!ensure(FBase64::Decode(AesKey, AesKeyBits)) ||
		!ensure(AesKeyBits.Num() == 32))
	{
		Fail("Failed to download Voxel Plugin: invalid AES key");
		return;
	}

	FAES::FAESKey FinalAesKey;
	FMemory::Memcpy(FinalAesKey.Key, AesKeyBits.GetData(), 32);

	FAES::DecryptData(Data.GetData(), Data.Num(), FinalAesKey);

	TArray64<uint8> UncompressedData;
	if (!FOodleCompressedArray::DecompressToTArray64(UncompressedData, Data))
	{
		Fail("Failed to download Voxel Plugin: decompression failed");
		return;
	}

	TMap<FString, TArray64<uint8>> Files;
	const FString ZipError = FVoxelInstallerUtilities::Unzip(UncompressedData, Files);
	if (!ZipError.IsEmpty())
	{
		Fail("Failed to unzip Voxel Plugin: " + ZipError);
		return;
	}

	const FString DownloadPath =
			bInstallInEngine
			? FPaths::EngineIntermediateDir() / "Voxel"
			: FPaths::ProjectIntermediateDir() / "Voxel";

	if (!MakePathWriteable(FPaths::ConvertRelativePathToFull(DownloadPath)))
	{
		Fail("Failed to clear readonly flag on: " + FPaths::ConvertRelativePathToFull(DownloadPath));
		return;
	}

	if (!IFileManager::Get().DeleteDirectory(*DownloadPath, false, true))
	{
		Fail("Failed to delete directory: " + FPaths::ConvertRelativePathToFull(DownloadPath));
		return;
	}

	// Check read-only status for download parent directory
	if (!MakePathWriteable(FPaths::ConvertRelativePathToFull(DownloadPath)))
	{
		Fail("Failed to clear readonly flag on: " + FPaths::ConvertRelativePathToFull(DownloadPath));
		return;
	}

	if (!IFileManager::Get().MakeDirectory(*DownloadPath, true))
	{
		Fail("Failed to create directory: " + FPaths::ConvertRelativePathToFull(DownloadPath));
		return;
	}

	for (const auto& It : Files)
	{
		const FString Path = DownloadPath / It.Key;

		IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), true);

		if (!ensure(FFileHelper::SaveArrayToFile(It.Value, *Path)))
		{
			Fail("Failed to write " + Path);
			return;
		}
	}

	const FString DialogPath = FPaths::ConvertRelativePathToFull(
		IPluginManager::Get().FindPlugin("VoxelPluginInstaller")->GetBaseDir() /
		"Source" /
		"DotNet" /
		(PLATFORM_WINDOWS ? "VoxelPluginInstallDialog-Win64.dll" : "VoxelPluginInstallDialog-Mac.app"));

	const FString DialogPackPath = DialogPath + ".pack";
	const FString DialogExePath = PLATFORM_WINDOWS ? DialogPath : DialogPath / "Contents" / "MacOS" / "VoxelPluginInstallDialog";

	if (PLATFORM_WINDOWS)
	{
		if (FPlatformMisc::IsDebuggerPresent() &&
			IFileManager::Get().FileExists(*DialogPath) &&
			!IFileManager::Get().FileExists(*DialogPackPath))
		{
			TArray64<uint8> Result;
			verify(FFileHelper::LoadFileToArray(Result, *DialogPath));

			TArray64<uint8> CompressedPackData;
			verify(FOodleCompressedArray::CompressTArray64(
				CompressedPackData,
				Result,
				FOodleDataCompression::ECompressor::Leviathan,
				FOodleDataCompression::ECompressionLevel::Optimal4));

			verify(FFileHelper::SaveArrayToFile(CompressedPackData, *DialogPackPath));
		}

		if (!IFileManager::Get().FileExists(*DialogPath))
		{
			if (!ensure(IFileManager::Get().FileExists(*DialogPackPath)))
			{
				Fail("Missing VoxelPluginInstallDialog");
				return;
			}

			TArray64<uint8> Result;
			if (!ensure(FFileHelper::LoadFileToArray(Result, *DialogPackPath)))
			{
				Fail("Failed to load VoxelPluginInstallDialog");
				return;
			}

			TArray64<uint8> UncompressedPackData;
			if (!FOodleCompressedArray::DecompressToTArray64(UncompressedPackData, Result))
			{
				Fail("VoxelPluginInstallDialog decompression failed");
				return;
			}

			if (!ensure(FFileHelper::SaveArrayToFile(UncompressedPackData, *DialogPath)))
			{
				Fail("Failed to save " + DialogPath);
				return;
			}
		}
	}
	else
	{
		if (FPlatformMisc::IsDebuggerPresent() &&
			IFileManager::Get().DirectoryExists(*DialogPath) &&
			!IFileManager::Get().FileExists(*DialogPackPath))
		{
			TMap<FString, TArray<uint8>> PathToData;
			IFileManager::Get().IterateDirectoryRecursively(*DialogPath, [&](const TCHAR* Path, const bool bIsDirectory)
			{
				if (bIsDirectory)
				{
					return true;
				}

				TArray<uint8> Result;
				verify(FFileHelper::LoadFileToArray(Result, Path));

				FString RelativePath = Path;
				verify(RelativePath.RemoveFromStart(DialogPath));
				verify(RelativePath.RemoveFromStart("/"));
				PathToData.Add(RelativePath, Result);

				return true;
			});

			TArray<uint8> Result;
			{
				FMemoryWriter Writer(Result);
				Writer << PathToData;
			}

			TArray<uint8> CompressedPackData;
			verify(FOodleCompressedArray::CompressTArray(
				CompressedPackData,
				Result,
				FOodleDataCompression::ECompressor::Leviathan,
				FOodleDataCompression::ECompressionLevel::Optimal4));

			verify(FFileHelper::SaveArrayToFile(CompressedPackData, *DialogPackPath));
		}

		if (!IFileManager::Get().DirectoryExists(*DialogPath))
		{
			if (!ensure(IFileManager::Get().FileExists(*DialogPackPath)))
			{
				Fail("Missing VoxelPluginInstallDialog");
				return;
			}

			TArray<uint8> Result;
			if (!ensure(FFileHelper::LoadFileToArray(Result, *DialogPackPath)))
			{
				Fail("Failed to load VoxelPluginInstallDialog");
				return;
			}

			TArray<uint8> UncompressedPackData;
			if (!FOodleCompressedArray::DecompressToTArray(UncompressedPackData, Result))
			{
				Fail("VoxelPluginInstallDialog decompression failed");
				return;
			}

			FMemoryReader Reader(UncompressedPackData);

			TMap<FString, TArray<uint8>> PathToData;
			Reader << PathToData;

			if (!ensure(!Reader.GetError()) ||
				!ensure(Reader.AtEnd()))
			{
				Fail("Failed to unpack VoxelPluginInstallDialog");
				return;
			}

			for (const auto& It : PathToData)
			{
				const FString Path = DialogPath / It.Key;

				if (!ensure(FFileHelper::SaveArrayToFile(It.Value, *Path)))
				{
					Fail("Failed to save " + Path);
					return;
				}
			}
		}
	}

#if PLATFORM_MAC
	chmod(TCHAR_TO_UTF8(*DialogExePath), S_IRWXU | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH);
#endif

	FString FullInstallLocation = FPaths::ConvertRelativePathToFull(InstallLocation);
	FString Json;
	{
		const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("EditorPID"), int64(FPlatformProcess::GetCurrentProcessId()));
		Writer->WriteValue(TEXT("EditorWorkingDirectory"), FPaths::ConvertRelativePathToFull(FPlatformProcess::GetCurrentWorkingDirectory()));
		Writer->WriteValue(TEXT("EditorExecutablePath"), FPlatformProcess::ExecutablePath());
		Writer->WriteValue(TEXT("EditorCommandLine"), FString(FCommandLine::GetOriginal()) + " -ShowVoxelExamples");
		Writer->WriteValue(TEXT("DownloadPath"), FPaths::ConvertRelativePathToFull(DownloadPath));
		Writer->WriteValue(TEXT("InstallLocation"), FullInstallLocation);
		Writer->WriteObjectEnd();
		Writer->Close();
	}

	if (!MakePathWriteable(FullInstallLocation))
	{
		Fail("Failed to clear readonly flag on: " + FullInstallLocation);
		return;
	}

	const FString JsonPath = FPaths::ConvertRelativePathToFull(FPaths::ProjectIntermediateDir() / "VoxelInstaller.json");

	if (!MakePathWriteable(JsonPath))
	{
		Fail("Failed to clear readonly flag on: " + FullInstallLocation);
		return;
	}

	ensure(FFileHelper::SaveStringToFile(Json, *JsonPath));

	const FString Args = FString::Printf(TEXT("\"%s\" -detach"), *JsonPath);

	FString StdOut;
	FString StdErr;
	int32 ReturnCode = 0;
	if (!FPlatformProcess::ExecProcess(
		*DialogExePath,
		*Args,
		&ReturnCode,
		&StdOut,
		&StdErr,
		*FPaths::ProjectDir()))
	{
		// ERROR_ELEVATION_REQUIRED (740): the installer dialog needs administrator rights
		// (eg when installing into the engine under Program Files), but the editor isn't
		// elevated. CreateProcess cannot launch an elevated child from a non-elevated
		// parent, so relaunch through ShellExecute's "runas" verb to trigger a UAC prompt.
		// This is why running the editor as admin "fixes" the install - we shouldn't require it.
		if (ReturnCode == 740)
		{
			// The dialog ships as a renamed .dll so CreateProcess can launch it directly, but
			// ShellExecute's "runas" verb resolves by file association and has no handler for
			// .dll ("the file does not have an app associated with it"). Copy it to a real .exe
			// in a writeable location so the elevated launch works.
			const FString ElevatedExePath = FPaths::ConvertRelativePathToFull(FPaths::ProjectIntermediateDir() / "VoxelPluginInstaller.exe");

			if (!MakePathWriteable(ElevatedExePath) ||
				IFileManager::Get().Copy(*ElevatedExePath, *DialogExePath, true, true) != COPY_OK)
			{
				Fail("Failed to prepare Voxel Plugin Installer for elevated launch");
				return;
			}

			int32 ElevatedReturnCode = 0;
			if (!FPlatformProcess::ExecElevatedProcess(
				*ElevatedExePath,
				*Args,
				&ElevatedReturnCode))
			{
				Fail("Failed to start Voxel Plugin Installer: administrator rights are required to install at this location");
				return;
			}
		}
		else
		{
			ensure(false);
			Fail("Failed to start Voxel Plugin Installer");
			return;
		}
	}

	// Disable all plugins
	for (const FVoxelPluginApi::FPluginInfo& PluginInfo : GVoxelPluginApi->GetInstalledPlugins())
	{
		FText FailMessage;
		if (!IProjectManager::Get().SetPluginEnabled(
			PluginInfo.Plugin->GetName(),
			true,
			FailMessage))
		{
			FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
		}
	}

	// Enable plugin if installed in engine
	if (bInstallInEngine)
	{
		FText FailMessage;
		if (!IProjectManager::Get().SetPluginEnabled(
			"Voxel",
			true,
			FailMessage))
		{
			FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
		}
	}

	// Save project file
	FText FailMessage;
	if (IProjectManager::Get().IsCurrentProjectDirty())
	{
		FGameProjectGenerationModule::Get().TryMakeProjectFileWriteable(FPaths::GetProjectFilePath());

		if (!IProjectManager::Get().SaveCurrentProjectToDisk(FailMessage))
		{
			FMessageDialog::Open(EAppMsgType::Ok, FailMessage);
		}
	}

	if (FMessageDialog::Open(
		EAppMsgType::YesNo,
		FText::FromString("Voxel Plugin successfully downloaded. Do you want to restart now to reload the plugin?")) == EAppReturnType::Yes)
	{
		GEngine->DeferredCommands.Add(TEXT("CLOSE_SLATE_MAINFRAME"));
	}
}

bool FVoxelPluginDownload::MakePathWriteable(FString Path)
{
	if (!IFileManager::Get().FileExists(*Path))
	{
		// Walk up the hierarchy to find the existing folder, to check if it will be non-read-only
		while (!IFileManager::Get().DirectoryExists(*Path))
		{
			Path = FPaths::ConvertRelativePathToFull(Path / "..");
		}
	}

	if (!IFileManager::Get().IsReadOnly(*Path))
	{
		return true;
	}

	const auto CheckoutFile = [&]
	{
		ISourceControlProvider & Provider = ISourceControlModule::Get().GetProvider();
		if (!Provider.IsEnabled())
		{
			return;
		}

		const TSharedPtr<ISourceControlState> NewState = Provider.GetState(*Path, EStateCacheUsage::ForceUpdate);
		if (!NewState ||
			!NewState->IsSourceControlled() ||
			NewState->IsCheckedOut() ||
			!NewState->CanCheckout())
		{
			return;
		}

		TArray<FString> FilesToBeCheckedOut;
		FilesToBeCheckedOut.Add(Path);
		Provider.Execute(ISourceControlOperation::Create<FCheckOut>(), FilesToBeCheckedOut);
	};
	CheckoutFile();

	if (!IFileManager::Get().IsReadOnly(*Path))
	{
		return true;
	}

	if (!ensure(FPlatformFileManager::Get().GetPlatformFile().SetReadOnly(*Path, false)))
	{
		return false;
	}

	return true;
}