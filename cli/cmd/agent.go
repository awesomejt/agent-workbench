package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var agentCmd = &cobra.Command{
	Use:   "agent",
	Short: "Manage agents in the registry",
}

var agentListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all registered agents",
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		list, err := client.ListAgents(1, 100)
		if err != nil {
			return render.Err("list agents: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no agents registered")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, a := range list.Items {
			rows[i] = []string{
				a.ID[:8],
				a.Name,
				render.Str(a.AgentType, "-"),
				render.Str(a.DefaultModel, "-"),
			}
		}
		render.Table([]string{"ID", "NAME", "TYPE", "MODEL"}, rows)
		return nil
	},
}

var agentCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Register a new agent",
	RunE: func(cmd *cobra.Command, args []string) error {
		name, _ := cmd.Flags().GetString("name")
		if name == "" {
			return render.Err("--name is required")
		}
		agentType, _ := cmd.Flags().GetString("type")
		model, _ := cmd.Flags().GetString("model")
		notes, _ := cmd.Flags().GetString("notes")

		body := map[string]any{"name": name}
		if agentType != "" {
			body["agent_type"] = agentType
		}
		if model != "" {
			body["default_model"] = model
		}
		if notes != "" {
			body["runtime_notes"] = notes
		}

		client := newClient()
		agent, err := client.CreateAgent(body)
		if err != nil {
			return render.Err("create agent: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(agent)
		}
		printAgent(agent)
		return nil
	},
}

var agentGetCmd = &cobra.Command{
	Use:   "get <agent-id>",
	Short: "Show details for an agent",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		agent, err := client.GetAgent(args[0])
		if err != nil {
			return render.Err("get agent: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(agent)
		}
		printAgent(agent)
		return nil
	},
}

var agentUpdateCmd = &cobra.Command{
	Use:   "update <agent-id>",
	Short: "Update an agent's metadata",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		version, _ := cmd.Flags().GetInt("version")
		if version == 0 {
			return render.Err("--version is required")
		}

		body := map[string]any{"version": version}
		if v, _ := cmd.Flags().GetString("name"); v != "" {
			body["name"] = v
		}
		if v, _ := cmd.Flags().GetString("type"); v != "" {
			body["agent_type"] = v
		}
		if v, _ := cmd.Flags().GetString("model"); v != "" {
			body["default_model"] = v
		}
		if v, _ := cmd.Flags().GetString("notes"); v != "" {
			body["runtime_notes"] = v
		}

		client := newClient()
		agent, err := client.UpdateAgent(args[0], body)
		if err != nil {
			return render.Err("update agent: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(agent)
		}
		printAgent(agent)
		return nil
	},
}

func printAgent(a api.Agent) {
	render.Line("ID:      %s", a.ID)
	render.Line("Name:    %s", a.Name)
	render.Line("Type:    %s", render.Str(a.AgentType, "-"))
	render.Line("Model:   %s", render.Str(a.DefaultModel, "-"))
	if a.RuntimeNotes != nil {
		render.Line("Notes:   %s", *a.RuntimeNotes)
	}
	render.Line("Version: %d", a.Version)
	render.Line("Updated: %s", a.UpdatedAt)
}

func init() {
	rootCmd.AddCommand(agentCmd)
	agentCmd.AddCommand(agentListCmd)
	agentCmd.AddCommand(agentCreateCmd)
	agentCmd.AddCommand(agentGetCmd)
	agentCmd.AddCommand(agentUpdateCmd)

	agentCreateCmd.Flags().String("name", "", "Agent name (required, must be unique)")
	agentCreateCmd.Flags().String("type", "", "Agent type (e.g. claude, openai, local)")
	agentCreateCmd.Flags().String("model", "", "Default model ID")
	agentCreateCmd.Flags().String("notes", "", "Runtime notes or hints")

	agentUpdateCmd.Flags().Int("version", 0, "Current version (required for optimistic locking)")
	agentUpdateCmd.Flags().String("name", "", "New name")
	agentUpdateCmd.Flags().String("type", "", "New agent type")
	agentUpdateCmd.Flags().String("model", "", "New default model ID")
	agentUpdateCmd.Flags().String("notes", "", "New runtime notes")
}
