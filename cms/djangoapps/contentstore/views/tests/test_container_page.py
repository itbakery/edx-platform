"""
Unit tests for the container page.
"""

from contentstore.utils import compute_publish_state, PublishState
from contentstore.views.tests.utils import StudioPageTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import ItemFactory


class ContainerPageTestCase(StudioPageTestCase):
    """
    Unit tests for the container page.
    """

    def setUp(self):
        super(ContainerPageTestCase, self).setUp()
        self.vertical = ItemFactory.create(parent_location=self.sequential.location,
                                           category='vertical', display_name='Unit')
        self.child_vertical = ItemFactory.create(parent_location=self.vertical.location,
                                                 category='vertical', display_name='Child Vertical')
        self.video = ItemFactory.create(parent_location=self.child_vertical.location,
                                        category="video", display_name="My Video")

    def test_container_html(self):
        branch_name = "MITx.999.Robot_Super_Course/branch/draft/block"
        self._test_html_content(
            self.child_vertical,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                'data-locator="{branch_name}/Child_Vertical">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Child Vertical</a>'
            ).format(branch_name=branch_name)
        )

    def test_container_on_container_html(self):
        """
        Create the scenario of an xblock with children (non-vertical) on the container page.
        This should create a container page that is a child of another container page.
        """
        published_container = ItemFactory.create(
            parent_location=self.child_vertical.location,
            category="wrapper", display_name="Wrapper"
        )
        ItemFactory.create(
            parent_location=published_container.location,
            category="html", display_name="Child HTML"
        )
        branch_name = "MITx.999.Robot_Super_Course/branch/draft/block"
        self._test_html_content(
            published_container,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                'data-locator="{branch_name}/Wrapper">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="/container/{branch_name}/Child_Vertical"\s*'
                r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'
            ).format(branch_name=branch_name)
        )

        # Now make the unit and its children into a draft and validate the container again
        modulestore('draft').convert_to_draft(self.vertical.location)
        modulestore('draft').convert_to_draft(self.child_vertical.location)
        draft_container = modulestore('draft').convert_to_draft(published_container.location)
        self._test_html_content(
            draft_container,
            branch_name=branch_name,
            expected_section_tag=(
                '<section class="wrapper-xblock level-page is-hidden studio-xblock-wrapper" '
                'data-locator="{branch_name}/Wrapper">'.format(branch_name=branch_name)
            ),
            expected_breadcrumbs=(
                r'<a href="/unit/{branch_name}/Unit"\s*'
                r'class="navigation-link navigation-parent">Unit</a>\s*'
                r'<a href="/container/{branch_name}/Child_Vertical"\s*'
                r'class="navigation-link navigation-parent">Child Vertical</a>\s*'
                r'<a href="#" class="navigation-link navigation-current">Wrapper</a>'
            ).format(branch_name=branch_name)
        )

    def _test_html_content(self, xblock, branch_name, expected_section_tag, expected_breadcrumbs):
        """
        Get the HTML for a container page and verify the section tag is correct
        and the breadcrumbs trail is correct.
        """
        html = self.get_page_html(xblock)
        publish_state = compute_publish_state(xblock)
        self.assertIn(expected_section_tag, html)
        # Verify the navigation link at the top of the page is correct.
        self.assertRegexpMatches(html, expected_breadcrumbs)

        # Verify the link that allows users to change publish status.
        expected_message = None
        if publish_state == PublishState.public:
            expected_message = 'you need to edit unit <a href="/unit/{branch_name}/Unit">Unit</a> as a draft.'
        else:
            expected_message = 'your changes will be published with unit <a href="/unit/{branch_name}/Unit">Unit</a>.'
        expected_unit_link = expected_message.format(
            branch_name=branch_name
        )
        self.assertIn(expected_unit_link, html)

    def test_public_container_preview_html(self):
        """
        Verify that a public xblock's container preview returns the expected HTML.
        """
        self.validate_preview_html(self.vertical, 'container_preview', is_editable=False, can_add=False)
        self.validate_preview_html(self.child_vertical, 'container_child_preview', is_editable=False, can_add=False)

    def test_draft_container_preview_html(self):
        """
        Verify that a draft xblock's container preview returns the expected HTML.
        """
        draft_unit = modulestore('draft').convert_to_draft(self.vertical.location)
        draft_container = modulestore('draft').convert_to_draft(self.child_vertical.location)
        self.validate_preview_html(draft_unit, 'container_preview')
        self.validate_preview_html(draft_container, 'container_child_preview')
