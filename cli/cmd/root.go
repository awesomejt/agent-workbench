package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	"agent-workbench/cli/internal/api"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var rootCmd = &cobra.Command{
	Use:   "awb",
	Short: "Agent Workbench CLI",
	Long:  "Coordinate AI agent tasks, view project status, and manage runs.",
}

// Execute is the entry point called from main.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// newClient builds an API client from the resolved Viper config.
func newClient() *api.Client {
	return api.New(viper.GetString("api_url"))
}

func init() {
	cobra.OnInitialize(initConfig)

	rootCmd.PersistentFlags().String("api-url", "http://localhost:8000", "API base URL ($AWB_API_URL)")
	rootCmd.PersistentFlags().String("project", "", "Project slug ($AWB_PROJECT)")
	rootCmd.PersistentFlags().String("agent", "", "Agent name ($AWB_AGENT)")
	rootCmd.PersistentFlags().StringP("output", "o", "table", "Output format: table or json")

	viper.BindPFlag("api_url", rootCmd.PersistentFlags().Lookup("api-url"))   //nolint:errcheck
	viper.BindPFlag("project", rootCmd.PersistentFlags().Lookup("project"))   //nolint:errcheck
	viper.BindPFlag("agent", rootCmd.PersistentFlags().Lookup("agent"))       //nolint:errcheck
	viper.BindPFlag("output", rootCmd.PersistentFlags().Lookup("output"))     //nolint:errcheck

	viper.SetEnvPrefix("AWB")
	viper.AutomaticEnv()
}

func initConfig() {
	viper.SetConfigName("config")
	// No SetConfigType — Viper auto-detects yaml, json, toml, etc.
	if home, err := os.UserHomeDir(); err == nil {
		viper.AddConfigPath(filepath.Join(home, ".config", "awb"))
		viper.AddConfigPath(filepath.Join(home, ".config", "agent-workbench"))
	}
	viper.AddConfigPath(".")
	_ = viper.ReadInConfig() // config file is optional
}

// requireFlag aborts with a usage error if the named flag is empty.
func requireFlag(cmd *cobra.Command, name string) (string, error) {
	v := viper.GetString(name)
	if v == "" {
		return "", fmt.Errorf("--%s is required (or set AWB_%s)", name, upcase(name))
	}
	return v, nil
}

func upcase(s string) string {
	result := make([]byte, len(s))
	for i := range s {
		if s[i] == '-' || s[i] == '_' {
			result[i] = '_'
		} else if s[i] >= 'a' && s[i] <= 'z' {
			result[i] = s[i] - 32
		} else {
			result[i] = s[i]
		}
	}
	return string(result)
}
