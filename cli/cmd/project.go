package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var projectCmd = &cobra.Command{
	Use:   "project",
	Short: "Manage projects",
}

var projectListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all projects",
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		list, err := client.ListProjects(1, 100)
		if err != nil {
			return render.Err("list projects: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no projects found")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, p := range list.Items {
			rows[i] = []string{
				p.Slug,
				p.Name,
				p.ProjectType,
				p.Environment,
				render.Str(p.LocalPath, "-"),
			}
		}
		render.Table([]string{"SLUG", "NAME", "TYPE", "ENV", "LOCAL PATH"}, rows)
		return nil
	},
}

var projectGetCmd = &cobra.Command{
	Use:   "get",
	Short: "Show details for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}
		// Fetch full record by ID (includes all fields).
		full, err := client.GetProject(project.ID)
		if err != nil {
			return render.Err("get project: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(full)
		}
		printProject(full)
		return nil
	},
}

var projectCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new project",
	RunE: func(cmd *cobra.Command, args []string) error {
		name, _ := cmd.Flags().GetString("name")
		slug, _ := cmd.Flags().GetString("slug")
		if name == "" || slug == "" {
			return render.Err("--name and --slug are required")
		}

		body := map[string]any{"name": name, "slug": slug}
		if v, _ := cmd.Flags().GetString("type"); v != "" {
			body["project_type"] = v
		}
		if v, _ := cmd.Flags().GetString("env"); v != "" {
			body["environment"] = v
		}
		if v, _ := cmd.Flags().GetString("path"); v != "" {
			body["local_path"] = v
		}
		if v, _ := cmd.Flags().GetString("git-remote"); v != "" {
			body["git_remote_url"] = v
		}
		if v, _ := cmd.Flags().GetString("default-agent"); v != "" {
			body["default_agent"] = v
		}

		client := newClient()
		project, err := client.CreateProject(body)
		if err != nil {
			return render.Err("create project: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(project)
		}
		printProject(project)
		return nil
	},
}

var projectUpdateCmd = &cobra.Command{
	Use:   "update",
	Short: "Update a project's metadata",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		version, _ := cmd.Flags().GetInt("version")
		if version == 0 {
			return render.Err("--version is required")
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		body := map[string]any{"version": version}
		if v, _ := cmd.Flags().GetString("name"); v != "" {
			body["name"] = v
		}
		if v, _ := cmd.Flags().GetString("type"); v != "" {
			body["project_type"] = v
		}
		if v, _ := cmd.Flags().GetString("env"); v != "" {
			body["environment"] = v
		}
		if v, _ := cmd.Flags().GetString("path"); v != "" {
			body["local_path"] = v
		}
		if v, _ := cmd.Flags().GetString("git-remote"); v != "" {
			body["git_remote_url"] = v
		}
		if v, _ := cmd.Flags().GetString("default-agent"); v != "" {
			body["default_agent"] = v
		}

		updated, err := client.UpdateProject(project.ID, body)
		if err != nil {
			return render.Err("update project: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(updated)
		}
		printProject(updated)
		return nil
	},
}

func printProject(p api.Project) {
	render.Line("ID:            %s", p.ID)
	render.Line("Name:          %s", p.Name)
	render.Line("Slug:          %s", p.Slug)
	render.Line("Type:          %s", p.ProjectType)
	render.Line("Environment:   %s", p.Environment)
	render.Line("Local path:    %s", render.Str(p.LocalPath, "-"))
	render.Line("Git remote:    %s", render.Str(p.GitRemoteURL, "-"))
	render.Line("Default agent: %s", render.Str(p.DefaultAgent, "-"))
	render.Line("Version:       %d", p.Version)
	render.Line("Updated:       %s", p.UpdatedAt)
}

func init() {
	rootCmd.AddCommand(projectCmd)
	projectCmd.AddCommand(projectListCmd)
	projectCmd.AddCommand(projectGetCmd)
	projectCmd.AddCommand(projectCreateCmd)
	projectCmd.AddCommand(projectUpdateCmd)

	projectCreateCmd.Flags().String("name", "", "Project display name (required)")
	projectCreateCmd.Flags().String("slug", "", "URL-safe project slug (required, unique)")
	projectCreateCmd.Flags().String("type", "", "Project type (e.g. service, library, tool)")
	projectCreateCmd.Flags().String("env", "", "Environment (local, dev, stage, prod)")
	projectCreateCmd.Flags().String("path", "", "Local filesystem path")
	projectCreateCmd.Flags().String("git-remote", "", "Git remote URL")
	projectCreateCmd.Flags().String("default-agent", "", "Default agent name for this project")

	projectUpdateCmd.Flags().Int("version", 0, "Current version (required for optimistic locking)")
	projectUpdateCmd.Flags().String("name", "", "New display name")
	projectUpdateCmd.Flags().String("type", "", "New project type")
	projectUpdateCmd.Flags().String("env", "", "New environment")
	projectUpdateCmd.Flags().String("path", "", "New local path")
	projectUpdateCmd.Flags().String("git-remote", "", "New git remote URL")
	projectUpdateCmd.Flags().String("default-agent", "", "New default agent name")
}
