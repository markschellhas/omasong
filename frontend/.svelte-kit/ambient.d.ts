
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```bash
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const NVM_INC: string;
	export const test_drop2_uk_prod_api_clientsecret: string;
	export const test_drop2_int_au_config_url_api: string;
	export const LDFLAGS: string;
	export const test_drop2_int_au_api_clientid: string;
	export const test_drop2_uk_stg_api_clientid: string;
	export const test_int_ca_api_clientsecret: string;
	export const TERM_PROGRAM: string;
	export const NODE: string;
	export const test_ipe16_us_api_clientsecret: string;
	export const INIT_CWD: string;
	export const NVM_CD_FLAGS: string;
	export const TERM: string;
	export const SHELL: string;
	export const test_drop2_int_stg_au_api_clientsecret: string;
	export const npm_config_metrics_registry: string;
	export const HOMEBREW_REPOSITORY: string;
	export const CPPFLAGS: string;
	export const TMPDIR: string;
	export const npm_config_global_prefix: string;
	export const LIBRARY_PATH: string;
	export const test_drop2_int_prod_au_authtoken_url_api: string;
	export const TERM_PROGRAM_VERSION: string;
	export const de_mte_config_url_api: string;
	export const test_ipe16_us_config_url_api: string;
	export const ZDOTDIR: string;
	export const test_drop2_int_stg_au_config_url_api: string;
	export const CURSOR_TRACE_ID: string;
	export const ORIGINAL_XDG_CURRENT_DESKTOP: string;
	export const MallocNanoZone: string;
	export const COLOR: string;
	export const TERM_SESSION_ID: string;
	export const npm_config_noproxy: string;
	export const npm_config_local_prefix: string;
	export const test_drop2_int_uk_mte_api_clientsecret: string;
	export const NVM_DIR: string;
	export const USER: string;
	export const COMMAND_MODE: string;
	export const npm_config_globalconfig: string;
	export const test_ca_api_clientsecret: string;
	export const test_drop2_int_uk_mte_config_url_api: string;
	export const test_drop2_int_uk_mte_api_clientid: string;
	export const test_drop2_int_us_api_clientsecret: string;
	export const test_drop2_int_de_authtoken_url_api: string;
	export const test_drop2_uk_stg_config_url_api: string;
	export const de_mte_api_clientid: string;
	export const CPATH: string;
	export const test_int_ca_authtoken_url_api: string;
	export const SSH_AUTH_SOCK: string;
	export const VSCODE_PROFILE_INITIALIZED: string;
	export const __CF_USER_TEXT_ENCODING: string;
	export const npm_execpath: string;
	export const LIBTORCH: string;
	export const test_drop2_int_mte_au_authtoken_url_api: string;
	export const test_drop2_int_de_api_clientid: string;
	export const test_drop2_int_prod_au_config_url_api: string;
	export const test_drop2_int_uk_mte_authtoken_url_api: string;
	export const de_mte_api_clientsecret: string;
	export const PATH: string;
	export const test_drop2_int_prod_au_api_clientsecret: string;
	export const npm_package_json: string;
	export const _: string;
	export const test_drop2_int_us_api_clientid: string;
	export const test_ca_api_clientid: string;
	export const npm_config_userconfig: string;
	export const npm_config_init_module: string;
	export const USER_ZDOTDIR: string;
	export const __CFBundleIdentifier: string;
	export const npm_command: string;
	export const test_int_ca_api_clientid: string;
	export const test_int_ca_config_url_api: string;
	export const PWD: string;
	export const JAVA_HOME: string;
	export const test_drop2_int_au_api_clientsecret: string;
	export const npm_lifecycle_event: string;
	export const EDITOR: string;
	export const test_drop2_int_mte_au_api_clientsecret: string;
	export const npm_package_name: string;
	export const LANG: string;
	export const test_drop2_int_us_authtoken_url_api: string;
	export const prod01_ca_authtoken_url_api: string;
	export const VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
	export const test_drop2_int_de_api_clientsecret: string;
	export const XPC_FLAGS: string;
	export const test_drop2_int_mte_au_api_clientid: string;
	export const test_drop2_uk_stg_api_clientsecret: string;
	export const npm_config_node_gyp: string;
	export const RBENV_SHELL: string;
	export const npm_package_version: string;
	export const test_drop2_uk_stg_authtoken_url_api: string;
	export const test_drop2_uk_prod_api_clientid: string;
	export const XPC_SERVICE_NAME: string;
	export const VSCODE_INJECTION: string;
	export const test_drop2_int_de_config_url_api: string;
	export const SHLVL: string;
	export const HOME: string;
	export const VSCODE_GIT_ASKPASS_MAIN: string;
	export const test_ipe16_us_api_clientid: string;
	export const est_ca_authtoken_url_api: string;
	export const HOMEBREW_PREFIX: string;
	export const prod01_ca_api_clientid: string;
	export const prod01_ca_config_url_api: string;
	export const prod01_ca_api_clientsecret: string;
	export const npm_config_cache: string;
	export const LOGNAME: string;
	export const npm_lifecycle_script: string;
	export const test_ipe16_us_authtoken_url_api: string;
	export const VSCODE_GIT_IPC_HANDLE: string;
	export const test_drop2_int_stg_au_authtoken_url_api: string;
	export const LC_CTYPE: string;
	export const test_drop2_int_au_authtoken_url_api: string;
	export const NVM_BIN: string;
	export const de_mte_authtoken_url_api: string;
	export const GOPATH: string;
	export const test_drop2_uk_prod_config_url_api: string;
	export const PKG_CONFIG_PATH: string;
	export const npm_config_user_agent: string;
	export const test_drop2_uk_prod_authtoken_url_api: string;
	export const VSCODE_GIT_ASKPASS_NODE: string;
	export const GIT_ASKPASS: string;
	export const HOMEBREW_CELLAR: string;
	export const INFOPATH: string;
	export const test_ca_config_url_api: string;
	export const test_drop2_int_us_config_url_api: string;
	export const test_drop2_int_stg_au_api_clientid: string;
	export const test_drop2_int_prod_au_api_clientid: string;
	export const PYTHON: string;
	export const npm_node_execpath: string;
	export const npm_config_prefix: string;
	export const COLORTERM: string;
	export const NODE_ENV: string;
}

/**
 * Similar to [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		NVM_INC: string;
		test_drop2_uk_prod_api_clientsecret: string;
		test_drop2_int_au_config_url_api: string;
		LDFLAGS: string;
		test_drop2_int_au_api_clientid: string;
		test_drop2_uk_stg_api_clientid: string;
		test_int_ca_api_clientsecret: string;
		TERM_PROGRAM: string;
		NODE: string;
		test_ipe16_us_api_clientsecret: string;
		INIT_CWD: string;
		NVM_CD_FLAGS: string;
		TERM: string;
		SHELL: string;
		test_drop2_int_stg_au_api_clientsecret: string;
		npm_config_metrics_registry: string;
		HOMEBREW_REPOSITORY: string;
		CPPFLAGS: string;
		TMPDIR: string;
		npm_config_global_prefix: string;
		LIBRARY_PATH: string;
		test_drop2_int_prod_au_authtoken_url_api: string;
		TERM_PROGRAM_VERSION: string;
		de_mte_config_url_api: string;
		test_ipe16_us_config_url_api: string;
		ZDOTDIR: string;
		test_drop2_int_stg_au_config_url_api: string;
		CURSOR_TRACE_ID: string;
		ORIGINAL_XDG_CURRENT_DESKTOP: string;
		MallocNanoZone: string;
		COLOR: string;
		TERM_SESSION_ID: string;
		npm_config_noproxy: string;
		npm_config_local_prefix: string;
		test_drop2_int_uk_mte_api_clientsecret: string;
		NVM_DIR: string;
		USER: string;
		COMMAND_MODE: string;
		npm_config_globalconfig: string;
		test_ca_api_clientsecret: string;
		test_drop2_int_uk_mte_config_url_api: string;
		test_drop2_int_uk_mte_api_clientid: string;
		test_drop2_int_us_api_clientsecret: string;
		test_drop2_int_de_authtoken_url_api: string;
		test_drop2_uk_stg_config_url_api: string;
		de_mte_api_clientid: string;
		CPATH: string;
		test_int_ca_authtoken_url_api: string;
		SSH_AUTH_SOCK: string;
		VSCODE_PROFILE_INITIALIZED: string;
		__CF_USER_TEXT_ENCODING: string;
		npm_execpath: string;
		LIBTORCH: string;
		test_drop2_int_mte_au_authtoken_url_api: string;
		test_drop2_int_de_api_clientid: string;
		test_drop2_int_prod_au_config_url_api: string;
		test_drop2_int_uk_mte_authtoken_url_api: string;
		de_mte_api_clientsecret: string;
		PATH: string;
		test_drop2_int_prod_au_api_clientsecret: string;
		npm_package_json: string;
		_: string;
		test_drop2_int_us_api_clientid: string;
		test_ca_api_clientid: string;
		npm_config_userconfig: string;
		npm_config_init_module: string;
		USER_ZDOTDIR: string;
		__CFBundleIdentifier: string;
		npm_command: string;
		test_int_ca_api_clientid: string;
		test_int_ca_config_url_api: string;
		PWD: string;
		JAVA_HOME: string;
		test_drop2_int_au_api_clientsecret: string;
		npm_lifecycle_event: string;
		EDITOR: string;
		test_drop2_int_mte_au_api_clientsecret: string;
		npm_package_name: string;
		LANG: string;
		test_drop2_int_us_authtoken_url_api: string;
		prod01_ca_authtoken_url_api: string;
		VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
		test_drop2_int_de_api_clientsecret: string;
		XPC_FLAGS: string;
		test_drop2_int_mte_au_api_clientid: string;
		test_drop2_uk_stg_api_clientsecret: string;
		npm_config_node_gyp: string;
		RBENV_SHELL: string;
		npm_package_version: string;
		test_drop2_uk_stg_authtoken_url_api: string;
		test_drop2_uk_prod_api_clientid: string;
		XPC_SERVICE_NAME: string;
		VSCODE_INJECTION: string;
		test_drop2_int_de_config_url_api: string;
		SHLVL: string;
		HOME: string;
		VSCODE_GIT_ASKPASS_MAIN: string;
		test_ipe16_us_api_clientid: string;
		est_ca_authtoken_url_api: string;
		HOMEBREW_PREFIX: string;
		prod01_ca_api_clientid: string;
		prod01_ca_config_url_api: string;
		prod01_ca_api_clientsecret: string;
		npm_config_cache: string;
		LOGNAME: string;
		npm_lifecycle_script: string;
		test_ipe16_us_authtoken_url_api: string;
		VSCODE_GIT_IPC_HANDLE: string;
		test_drop2_int_stg_au_authtoken_url_api: string;
		LC_CTYPE: string;
		test_drop2_int_au_authtoken_url_api: string;
		NVM_BIN: string;
		de_mte_authtoken_url_api: string;
		GOPATH: string;
		test_drop2_uk_prod_config_url_api: string;
		PKG_CONFIG_PATH: string;
		npm_config_user_agent: string;
		test_drop2_uk_prod_authtoken_url_api: string;
		VSCODE_GIT_ASKPASS_NODE: string;
		GIT_ASKPASS: string;
		HOMEBREW_CELLAR: string;
		INFOPATH: string;
		test_ca_config_url_api: string;
		test_drop2_int_us_config_url_api: string;
		test_drop2_int_stg_au_api_clientid: string;
		test_drop2_int_prod_au_api_clientid: string;
		PYTHON: string;
		npm_node_execpath: string;
		npm_config_prefix: string;
		COLORTERM: string;
		NODE_ENV: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
