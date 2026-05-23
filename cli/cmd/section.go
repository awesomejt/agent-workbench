package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var sectionCmd = &cobra.Command{
	Use:   "section",
	Short: "Manage project sections",
}

var sectionListCmd = &cobra.Command{
	Use:   "list",
	Short: "List sections for a project",
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

		list, err := client.ListSections(project.ID)
		if err != nil {
			return render.Err("list sections: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no sections found")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, s := range list.Items {
			rows[i] = []string{
				s.ID[:8],
				s.Slug,
				s.Name,
				s.SectionType,
				fmt.Sprintf("%d", s.SortOrder),
			}
		}
		render.Table([]string{"ID", "SLUG", "NAME", "TYPE", "ORDER"}, rows)
		return nil
	},
}

var sectionCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new section within a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		name, _ := cmd.Flags().GetString("name")
		sectionSlug, _ := cmd.Flags().GetString("slug")
		if name == "" || sectionSlug == "" {
			return render.Err("--name and --slug are required")
		}

		body := map[string]any{"name": name, "slug": sectionSlug}
		if v, _ := cmd.Flags().GetString("type"); v != "" {
			body["section_type"] = v
		}
		if v, _ := cmd.Flags().GetString("description"); v != "" {
			body["description"] = v
		}
		if v, _ := cmd.Flags().GetInt("order"); v != 0 {
			body["sort_order"] = v
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		section, err := client.CreateSection(project.ID, body)
		if err != nil {
			return render.Err("create section: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(section)
		}
		printSection(section)
		return nil
	},
}

var sectionGetCmd = &cobra.Command{
	Use:   "get <section-id>",
	Short: "Show details for a section",
	Args:  cobra.ExactArgs(1),
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

		section, err := client.GetSection(project.ID, args[0])
		if err != nil {
			return render.Err("get section: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(section)
		}
		printSection(section)
		return nil
	},
}

var sectionUpdateCmd = &cobra.Command{
	Use:   "update <section-id>",
	Short: "Update a section's metadata",
	Args:  cobra.ExactArgs(1),
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
		if v, _ := cmd.Flags().GetString("slug"); v != "" {
			body["slug"] = v
		}
		if v, _ := cmd.Flags().GetString("type"); v != "" {
			body["section_type"] = v
		}
		if v, _ := cmd.Flags().GetString("description"); v != "" {
			body["description"] = v
		}
		if v, _ := cmd.Flags().GetInt("order"); v != 0 {
			body["sort_order"] = v
		}

		section, err := client.UpdateSection(project.ID, args[0], body)
		if err != nil {
			return render.Err("update section: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(section)
		}
		printSection(section)
		return nil
	},
}

func printSection(s api.Section) {
	render.Line("ID:          %s", s.ID)
	render.Line("Name:        %s", s.Name)
	render.Line("Slug:        %s", s.Slug)
	render.Line("Type:        %s", s.SectionType)
	render.Line("Sort order:  %d", s.SortOrder)
	if s.Description != nil {
		render.Line("Description: %s", *s.Description)
	}
	render.Line("Version:     %d", s.Version)
	render.Line("Updated:     %s", s.UpdatedAt)
}

func init() {
	rootCmd.AddCommand(sectionCmd)
	sectionCmd.AddCommand(sectionListCmd)
	sectionCmd.AddCommand(sectionCreateCmd)
	sectionCmd.AddCommand(sectionGetCmd)
	sectionCmd.AddCommand(sectionUpdateCmd)

	sectionCreateCmd.Flags().String("name", "", "Section display name (required)")
	sectionCreateCmd.Flags().String("slug", "", "URL-safe section slug (required)")
	sectionCreateCmd.Flags().String("type", "", "Section type (default: module)")
	sectionCreateCmd.Flags().String("description", "", "Section description")
	sectionCreateCmd.Flags().Int("order", 0, "Sort order (lower = first)")

	sectionUpdateCmd.Flags().Int("version", 0, "Current version (required for optimistic locking)")
	sectionUpdateCmd.Flags().String("name", "", "New display name")
	sectionUpdateCmd.Flags().String("slug", "", "New slug")
	sectionUpdateCmd.Flags().String("type", "", "New section type")
	sectionUpdateCmd.Flags().String("description", "", "New description")
	sectionUpdateCmd.Flags().Int("order", 0, "New sort order")
}
