// Copyright Voxel Plugin SAS. All Rights Reserved.

#include "VoxelPluginApi.h"
#include "VoxelPluginDownload.h"
#include "VoxelInstallerSettings.h"
#include "HttpModule.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/ConfigCacheIni.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Framework/Notifications/NotificationManager.h"

FVoxelPluginApi* GVoxelPluginApi = nullptr;

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

FVoxelPluginApi::EState FVoxelPluginApi::GetPluginState() const
{
	const TOptional<FPluginInfo> EnabledPlugin = GetEnabledPlugin();

	if (!EnabledPlugin)
	{
		return EState::NotInstalled;
	}
	if (EnabledPlugin->bSourcePlugin)
	{
		return EState::SourcePlugin;
	}

	for (const TSharedPtr<FVoxelPluginVersion>& Version : GVoxelPluginApi->AllVersions)
	{
		if (!ensure(Version))
		{
			continue;
		}
		if (Version->GetBranch() == EnabledPlugin->Version.GetBranch() &&
			Version->GetCounter() > EnabledPlugin->Version.GetCounter())
		{
			return EState::HasUpdate;
		}
	}
	return EState::NoUpdate;
}

TOptional<FVoxelPluginApi::FPluginInfo> FVoxelPluginApi::GetEnabledPlugin() const
{
	TOptional<FPluginInfo> EnabledPlugin;
	for (const FPluginInfo& PluginInfo : GetInstalledPlugins())
	{
		if (PluginInfo.Plugin->IsEnabled())
		{
			ensure(!EnabledPlugin);
			EnabledPlugin = PluginInfo;
		}
	}
	return EnabledPlugin;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

bool FVoxelPluginApi::Tick(float DeltaTime)
{
	if (IsLoggedIn())
	{
		return true;
	}

	if (!Challenge.IsEmpty() &&
		LastChallengeTime + 1 < FPlatformTime::Seconds())
	{
		LastChallengeTime = FPlatformTime::Seconds();

		UE_LOG(LogVoxelInstaller, Log, TEXT("Querying challenge..."));

		MakeRequest(
			"auth/getChallengeToken?challenge=" + Challenge,
			{},
			ERequestVerb::Get,
			false,
			FHttpRequestCompleteDelegate::CreateLambda([this](
				const FHttpRequestPtr Request,
				const FHttpResponsePtr Response,
				const bool bConnectedSuccessfully)
				{
					if (!Response)
					{
						UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query token: No response"));
						return;
					}

					if (Response->GetResponseCode() == 404)
					{
						UE_LOG(LogVoxelInstaller, Log, TEXT("Challenge not found"));

						// Not ready yet
						NumChallengeAttempts++;
						if (NumChallengeAttempts > 500)
						{
							// Give up
							Challenge.Reset();
						}
						return;
					}

					if (!bConnectedSuccessfully ||
						Response->GetResponseCode() != 200)
					{
						UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query token: %d %s"), Response->GetResponseCode(), *Response->GetContentAsString());
						return;
					}

					UE_LOG(LogVoxelInstaller, Log, TEXT("Logged in successfully"));

					Token = Response->GetContentAsString().TrimStartAndEnd();
					Challenge.Reset();
					RefreshUser();
				}));
	}

	return true;
}

void FVoxelPluginApi::Initialize()
{
	RefreshUser();

	MakeRequest(
		"config",
		{},
		ERequestVerb::Get,
		false,
		FHttpRequestCompleteDelegate::CreateLambda([this](
			const FHttpRequestPtr Request,
			const FHttpResponsePtr Response,
			const bool bConnectedSuccessfully)
		{
			if (!Response)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query config: No response"));
				return;
			}

			if (!bConnectedSuccessfully ||
				Response->GetResponseCode() != 200)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query config: %d %s"), Response->GetResponseCode(), *Response->GetContentAsString());
				return;
			}

			const FString ConfigString = Response->GetContentAsString();

			TSharedPtr<FJsonObject> Object;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ConfigString);
			if (!ensure(FJsonSerializer::Deserialize(Reader, Object)) ||
				!ensure(Object))
			{
				return;
			}

			ensure(!bIsConfigReady);
			bIsConfigReady = true;

			Config = FVoxelConfig();
			Config->bShowLoginButton = Object->GetBoolField(TEXT("showLoginButton"));
		}));

	UpdateVersions();

	for (const TSharedRef<IPlugin>& Plugin : IPluginManager::Get().GetDiscoveredPlugins())
	{
		if (Plugin->GetName() != "Voxel" &&
			Plugin->GetName() != "Voxel-dev" &&
			!Plugin->GetName().StartsWith("Voxel-2"))
		{
			continue;
		}

		const FString VersionName = Plugin->GetDescriptor().VersionName;

		FPluginInfo PluginInfo;
		PluginInfo.Plugin = Plugin;

		if (VersionName == "Unknown")
		{
			PluginInfo.bSourcePlugin = true;
		}
		else
		{
			PluginInfo.Version.Parse(VersionName);
		}

		InstalledPlugins.Add(PluginInfo);
	}
}

void FVoxelPluginApi::RefreshUser()
{
	if (Token.IsEmpty())
	{
		FFileHelper::LoadFileToString(Token, *GetTokenPath());
		Token.TrimStartAndEndInline();
	}

	if (Token.IsEmpty())
	{
		return;
	}

	if (bIsRefreshingUser)
	{
		return;
	}
	bIsRefreshingUser = true;

	UE_LOG(LogVoxelInstaller, Log, TEXT("Refreshing user"));

	MakeRequest(
		"auth/refresh",
		{},
		ERequestVerb::Post,
		true,
		FHttpRequestCompleteDelegate::CreateLambda([this](
			const FHttpRequestPtr Request,
			const FHttpResponsePtr Response,
			const bool bConnectedSuccessfully)
		{
			ensure(bIsRefreshingUser);
			bIsRefreshingUser = false;

			if (!Response)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to login: No response"));
				return;
			}

			if (!bConnectedSuccessfully ||
				Response->GetResponseCode() != 201)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to login: %d %s"), Response->GetResponseCode(), *Response->GetContentAsString());
				return;
			}

			UpdateUser(Response->GetContentAsString());
		}));
}

void FVoxelPluginApi::UpdateVersions()
{
	if (bIsUpdatingVersions)
	{
		return;
	}
	bIsUpdatingVersions = true;

	UE_LOG(LogVoxelInstaller, Log, TEXT("Updating versions"));

	MakeRequest(
		"version/list",
		{},
		ERequestVerb::Get,
		false,
		FHttpRequestCompleteDelegate::CreateLambda([this](
			const FHttpRequestPtr Request,
			const FHttpResponsePtr Response,
			const bool bConnectedSuccessfully)
		{
			ensure(bIsUpdatingVersions);
			bIsUpdatingVersions = false;

			if (!Response)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query versions: No response"));
				return;
			}

			if (!bConnectedSuccessfully ||
				Response->GetResponseCode() != 200)
			{
				UE_LOG(LogVoxelInstaller, Error, TEXT("Failed to query versions: %d %s"), Response->GetResponseCode(), *Response->GetContentAsString());
				return;
			}

			UpdateVersions(Response->GetContentAsString());
		}));
}

void FVoxelPluginApi::Login()
{
	Challenge.Reset();
	for (int32 Index = 0; Index < 32; Index++)
	{
		Challenge += char(FMath::RandRange('A', 'Z'));
	}

	const FString Url = "https://new.voxelplugin.com/oauth?challenge=" + Challenge;
	UE_LOG(LogVoxelInstaller, Log, TEXT("Opening %s"), *Url);

	LastChallengeTime = FPlatformTime::Seconds();
	NumChallengeAttempts = 0;
	FPlatformProcess::LaunchURL(*Url, nullptr, nullptr);
}

void FVoxelPluginApi::Logout()
{
	UE_LOG(LogVoxelInstaller, Log, TEXT("Logging out"));

	Token = {};
	User.Reset();
	IFileManager::Get().Delete(*GetTokenPath());

	UpdateVersions(LastVersionsString);
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void FVoxelPluginApi::OpenReleaseNotes(const FVoxelPluginVersion& Version) const
{
	const FString Url = "https://docs.voxelplugin.com/release-notes#" + Version.ToString_MajorMinor();
	FPlatformProcess::LaunchURL(*Url, nullptr, nullptr);
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

FString FVoxelPluginApi::GetTokenPath() const
{
	return GetAppDataPath() / "Token.txt";
}

FString FVoxelPluginApi::GetAppDataPath() const
{
	if (PLATFORM_WINDOWS)
	{
		return FPlatformMisc::GetEnvironmentVariable(TEXT("LOCALAPPDATA")) / "UnrealEngine" / "VoxelPlugin";
	}
	else
	{
		ensure(PLATFORM_MAC);
		return FPlatformMisc::GetEnvironmentVariable(TEXT("HOME")) / "Library" / "Caches" / "UnrealEngine" / "VoxelPlugin";
	}
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void FVoxelPluginApi::MakeRequest(
	const FString& Endpoint,
	const TMap<FString, FString>& Parameters,
	const ERequestVerb Verb,
	const bool bNeedAuth,
	FHttpRequestCompleteDelegate OnComplete) const
{
	const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();

	FString Url = "https://api.voxelplugin.com/" + Endpoint + "?";

	if (bNeedAuth &&
		!Token.IsEmpty())
	{
		Url += "token=" + Token + "&";
	}

	for (auto& It : Parameters)
	{
		Url += It.Key + "=" + It.Value + "&";
	}

	Url.RemoveFromEnd("?");
	Url.RemoveFromEnd("&");

	HttpRequest->OnProcessRequestComplete() = OnComplete;
	HttpRequest->SetURL(Url);
	HttpRequest->SetVerb(Verb == ERequestVerb::Get ? "GET" : "POST");
	HttpRequest->ProcessRequest();
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void FVoxelPluginApi::UpdateUser(const FString& UserString)
{
	TSharedPtr<FJsonObject> ParsedObject;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(UserString);
	if (!ensure(FJsonSerializer::Deserialize(Reader, ParsedObject)) ||
		!ensure(ParsedObject))
	{
		return;
	}

	User = FVoxelUser();
	User->Id = ParsedObject->GetStringField(TEXT("id"));
	User->Email = ParsedObject->GetStringField(TEXT("email"));
	User->bHasValidLicense = ParsedObject->GetBoolField(TEXT("hasValidLicense"));

	Token = ParsedObject->GetStringField(TEXT("token"));
	ensure(!Token.IsEmpty());

	IFileManager::Get().MakeDirectory(*FPaths::GetPath(GetTokenPath()), true);
	ensure(FFileHelper::SaveStringToFile(Token, *GetTokenPath()));

	UpdateVersions(LastVersionsString);
}

void FVoxelPluginApi::UpdateVersions(const FString& VersionsString)
{
	LastVersionsString = VersionsString;

	if (!HasCompatibleLicense(SelectedVersion))
	{
		SelectedVersion = {};
	}

	if (VersionsString.IsEmpty())
	{
		return;
	}

	TSharedPtr<FJsonValue> ParsedValue;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(VersionsString);
	if (!ensure(FJsonSerializer::Deserialize(Reader, ParsedValue)) ||
		!ensure(ParsedValue))
	{
		return;
	}

	TArray<TSharedPtr<FVoxelPluginVersion>> NewVersions;
	for (const TSharedPtr<FJsonValue>& Value : ParsedValue->AsArray())
	{
		const FString VersionString = Value->AsString();

		FVoxelPluginVersion Version;
		if (!ensure(Version.Parse(VersionString)))
		{
			continue;
		}

		if (Version.Type == FVoxelPluginVersion::EType::Dev &&
			!GetDefault<UVoxelInstallerSettings>()->bShowDevVersions)
		{
			continue;
		}

		if (Version.bDebug &&
			!GetDefault<UVoxelInstallerSettings>()->bShowUnstableVersions)
		{
			continue;
		}

		if (!HasCompatibleLicense(Version))
		{
			continue;
		}

		if (Version.EngineVersion != ENGINE_MAJOR_VERSION * 100 + ENGINE_MINOR_VERSION)
		{
			continue;
		}

#if PLATFORM_WINDOWS
		if (Version.Platform != FVoxelPluginVersion::EPlatform::Win64)
		{
			continue;
		}
#elif PLATFORM_MAC
		if (Version.Platform != FVoxelPluginVersion::EPlatform::Mac)
		{
			continue;
		}
#endif

		NewVersions.Add(MakeShared<FVoxelPluginVersion>(Version));
	}

	if (AllVersions.Num() != NewVersions.Num())
	{
		SetVersions(NewVersions);
	}
	else
	{
		for (int32 Index = 0; Index < AllVersions.Num(); Index++)
		{
			if (*AllVersions[Index] == *NewVersions[Index])
			{
				continue;
			}

			SetVersions(NewVersions);
			break;
		}
	}

	if (SelectedVersion.Type == FVoxelPluginVersion::EType::Unknown)
	{
		const TOptional<FPluginInfo> EnabledPlugin = GetEnabledPlugin();

		for (const TSharedPtr<FVoxelPluginVersion>& Version : AllVersions)
		{
			if (EnabledPlugin &&
				!EnabledPlugin->bSourcePlugin &&
				EnabledPlugin->Version.GetBranch() != Version->GetBranch())
			{
				continue;
			}

			if (Version->GetCounter() > SelectedVersion.GetCounter())
			{
				SelectedVersion = *Version;
			}
		}
	}

	static bool bDisplayedNotification = false;
	if (bDisplayedNotification)
	{
		return;
	}
	bDisplayedNotification = true;

	if (GetPluginState() != EState::HasUpdate)
	{
		return;
	}

	const TOptional<FPluginInfo> EnabledPlugin = GetEnabledPlugin();
	if (!ensure(EnabledPlugin))
	{
		return;
	}

	FVoxelPluginVersion Latest = EnabledPlugin->Version;
	if (Latest.Type != FVoxelPluginVersion::EType::Preview &&
		Latest.Type != FVoxelPluginVersion::EType::Release)
	{
		return;
	}

	for (const TSharedPtr<FVoxelPluginVersion>& Version : GVoxelPluginApi->AllVersions)
	{
		if (!ensure(Version))
		{
			continue;
		}
		if (Version->GetBranch() == Latest.GetBranch() &&
			Version->GetCounter() > Latest.GetCounter())
		{
			Latest = *Version;
		}
	}

	FString String;
	if (GConfig->GetString(
		TEXT("VoxelPlugin_SkippedVersions"),
		*Latest.ToString_MajorMinor(),
		String,
		GEditorPerProjectIni) &&
		String == "1")
	{
		return;
	}

	const TSharedRef<TWeakPtr<SNotificationItem>> WeakNotification = MakeShared<TWeakPtr<SNotificationItem>>();

	FNotificationInfo Info(FText::Format(INVTEXT("A new Voxel Plugin release is available: {0}"), FText::FromString(Latest.ToString_MajorMinor())));

	Info.bFireAndForget = false;
	Info.ExpireDuration = 0.f;
	Info.FadeInDuration = 0.f;
	Info.FadeOutDuration = 0.f;
	Info.WidthOverride = FOptionalSize();

	Info.CheckBoxText = INVTEXT("Skip this update");
	Info.CheckBoxStateChanged = FOnCheckStateChanged::CreateLambda([=](const ECheckBoxState NewState)
	{
		GConfig->SetString(
			TEXT("VoxelPlugin_SkippedVersions"),
			*Latest.ToString_MajorMinor(),
			NewState == ECheckBoxState::Checked ? TEXT("1") : TEXT("0"),
			GEditorPerProjectIni);
	});

	Info.ButtonDetails.Add(FNotificationButtonInfo(
		INVTEXT("Update"),
		INVTEXT("Update Voxel Plugin to latest"),
		FSimpleDelegate::CreateLambda([=]
		{
			GVoxelAuthDownload->Download(Latest, EnabledPlugin->Plugin->GetLoadedFrom() == EPluginLoadedFrom::Engine);

			const TSharedPtr<SNotificationItem> Notification = WeakNotification->Pin();
			if (!ensure(Notification))
			{
				return;
			}

			Notification->ExpireAndFadeout();
		}),
		SNotificationItem::CS_None));

	Info.ButtonDetails.Add(FNotificationButtonInfo(
		INVTEXT("Release Notes"),
		INVTEXT("Show the new version release notes"),
		FSimpleDelegate::CreateLambda([=]
		{
			GVoxelPluginApi->OpenReleaseNotes(Latest);
		}),
		SNotificationItem::CS_None));

	Info.ButtonDetails.Add(FNotificationButtonInfo(
		INVTEXT("Dismiss"),
		INVTEXT("Dismiss"),
		FSimpleDelegate::CreateLambda([=]
		{
			const TSharedPtr<SNotificationItem> Notification = WeakNotification->Pin();
			if (!ensure(Notification))
			{
				return;
			}

			Notification->ExpireAndFadeout();
		}),
		SNotificationItem::CS_None));

	*WeakNotification = FSlateNotificationManager::Get().AddNotification(Info);
}

void FVoxelPluginApi::SetVersions(const TArray<TSharedPtr<FVoxelPluginVersion>>& NewVersions)
{
	AllVersions = NewVersions;

	VersionStringToVersion = {};
	VersionStringToVersion.Reserve(AllVersions.Num());
	for (const TSharedPtr<FVoxelPluginVersion>& Version : AllVersions)
	{
		VersionStringToVersion.Add(Version->ToString_API(), Version);
	}

	OnComboBoxesUpdated.Broadcast();
}