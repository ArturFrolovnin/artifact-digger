// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "VoxelMinimal.h"
#include "VoxelPluginVersion.h"
#include "Containers/Ticker.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IPluginManager.h"
#include "Modules/ModuleInterface.h"

class FVoxelPluginApi;

extern FVoxelPluginApi* GVoxelPluginApi;

class IVoxelEditorModule : public IModuleInterface
{
public:
	int32 Version = 0;

	virtual void ShowContent() = 0;
};

struct FVoxelConfig
{
	bool bShowLoginButton = false;
};

struct FVoxelUser
{
	FString Id;
	FString Email;
	bool bHasValidLicense = false;
};

class FVoxelPluginApi : public FTSTickerObjectBase
{
public:
	TArray<TSharedPtr<FVoxelPluginVersion>> AllVersions;
	TMap<FString, TSharedPtr<FVoxelPluginVersion>> VersionStringToVersion;
	FVoxelPluginVersion SelectedVersion;

	FSimpleMulticastDelegate OnComboBoxesUpdated;

	struct FPluginInfo
	{
		const TSharedRef<bool> IsDeleted = MakeShared<bool>(false);

		TSharedPtr<IPlugin> Plugin;
		bool bSourcePlugin = false;
		FVoxelPluginVersion Version;

		FString GetVersionDisplayString() const
		{
			if (bSourcePlugin)
			{
				return  "Source build";
			}
			return Version.ToString_UserFacing();
		}
	};
	const TArray<FPluginInfo>& GetInstalledPlugins() const
	{
		return InstalledPlugins;
	}

	enum class EState
	{
		NotInstalled,
		SourcePlugin,
		HasUpdate,
		NoUpdate
	};
	EState GetPluginState() const;
	TOptional<FPluginInfo> GetEnabledPlugin() const;

private:
	TArray<FPluginInfo> InstalledPlugins;

public:
    FVoxelPluginApi() = default;

	//~ Begin FTSTickerObjectBase Interface
	virtual bool Tick(float DeltaTime) override;
	//~ End FTSTickerObjectBase Interface

	void Initialize();
	void RefreshUser();
	void UpdateVersions();

public:
	void Login();
	void Logout();

	bool IsConfigReady() const
	{
		return bIsConfigReady;
	}
	bool IsRefreshingUser() const
	{
		return bIsRefreshingUser;
	}
	bool IsUpdatingVersions() const
	{
		return bIsUpdatingVersions;
	}
	bool IsLoggedIn() const
	{
		return User.IsSet();
	}
	bool HasLicense() const
	{
		return
			User &&
			User->bHasValidLicense;
	}
	bool HasCompatibleLicense(const FVoxelPluginVersion& Version) const
	{
		if (Version.bNoSource)
		{
			// We don't want pro downloading no-source versions
			return !HasLicense();
		}
		else
		{
			return HasLicense();
		}
	}

	FVoxelConfig GetConfig() const
	{
		ensure(Config);
		return Config.Get({});
	}
	FVoxelUser GetUser() const
	{
		ensure(User);
		return User.Get({});
	}

public:
	void OpenReleaseNotes(const FVoxelPluginVersion& Version) const;

	FString GetTokenPath() const;
	FString GetAppDataPath() const;

    enum class ERequestVerb
    {
	    Get,
        Post
    };
	void MakeRequest(
		const FString& Endpoint,
		const TMap<FString, FString>& Parameters,
		ERequestVerb Verb,
		bool bNeedAuth,
		FHttpRequestCompleteDelegate OnComplete) const;

private:
	bool bIsConfigReady = false;
	bool bIsRefreshingUser = false;
	bool bIsUpdatingVersions = false;

	double LastChallengeTime = 0;
	int32 NumChallengeAttempts = 0;
	FString LastVersionsString;

	FString Token;
	FString Challenge;
	TOptional<FVoxelConfig> Config;
	TOptional<FVoxelUser> User;

	void UpdateUser(const FString& UserString);
	void UpdateVersions(const FString& VersionsString);
	void SetVersions(const TArray<TSharedPtr<FVoxelPluginVersion>>& NewVersions);
};